"""Run a bounded OpenRouter pilot on PUBLIC RxSafeBench simulated dialogues.

Never point this runner at restricted MIMIC, eICU, or local patient files.
The API key is read only from OPENROUTER_API_KEY; no prompts or secrets are
written to the repository. This is multiple-choice benchmark performance,
not a clinical safety certification.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.request


API = "https://openrouter.ai/api/v1/chat/completions"
SOURCE_COMMIT = "a25f9a1f173cf034b678c60f051901e86fbbbbb2"
MODELS = ("openai/gpt-6.1-sol", "google/gemini-3.8-flash", "deepseek/deepseek-v4.1-flash")
PUBLIC_SHA256 = {
    "RxSafeBench_Contradiction.json": "e9e097408bbc9399768d88a04af3eac46674dac11af35251e51247453765446b",
    "RxSafeBench_Interaction.json": "d34cc05a98fe4120659b1a899d4cbf206e1a36cf0e1c4a3862efac0ea7f54fc9",
}


def verify_public_files(data_dir: Path) -> None:
    """Fail closed if the caller passes anything other than the pinned public data."""
    for name, expected in PUBLIC_SHA256.items():
        digest = hashlib.sha256()
        with (data_dir / name).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected:
            raise ValueError(f"Public benchmark checksum mismatch: {name}")


def load_cases(data_dir: Path, per_type: int) -> list[dict]:
    files = {"contraindication": "RxSafeBench_Contradiction.json",
             "interaction": "RxSafeBench_Interaction.json"}
    result = []
    for kind, filename in files.items():
        rows = json.loads((data_dir / filename).read_text())
        candidates = {}
        key = "Contradiction" if kind == "contraindication" else "interaction"
        for row in rows:
            for item in row[key]:
                digest = hashlib.sha256((kind + item["dialogue"] + item["med_true"]).encode()).hexdigest()
                candidates.setdefault(digest, (row, item))
        # Deduplicate repeated dialogues before hash sampling to avoid overweighting a scenario.
        for rank, digest in enumerate(sorted(candidates)[:per_type]):
            row, item = candidates[digest]
            true_pos = rank % 3
            options = [None] * 3
            options[true_pos] = item["med_true"]
            others = [item["med_false"], item["med_not_related"]]
            if int(digest[0], 16) % 2:
                others.reverse()
            for j in range(3):
                if options[j] is None:
                    options[j] = others.pop()
            result.append({"id": digest[:16], "type": kind, "indication": row.get("indication"),
                           "dialogue": item["dialogue"], "options": options,
                           "gold": "ABC"[true_pos],
                           "safe_name_in_dialogue": item["med_true"].lower() in item["dialogue"].lower()})
    return result


def query(model: str, case: dict, key: str, retries: int = 3) -> dict:
    if "question" in case:
        letters = "ABCD"
        prompt = ("This is a public research benchmark about medication reasoning. "
                  "Choose the single best answer. Respond with exactly one letter: A, B, C, or D.\n\n"
                  f"Question:\n{case['question']}\n\n"
                  + "\n".join(f"{letter}. {option}" for letter, option in zip(letters, case["options"]))
                  + "\n\nAnswer:")
    else:
        letters = "ABC"
        prompt = (
            "This is a research benchmark with a fictional consultation. Choose the single most appropriate "
            "medication among the three options based on the dialogue and medication safety. "
            "Respond with exactly one letter: A, B, or C.\n\n"
            f"Dialogue:\n{case['dialogue']}\n\n"
            + "\n".join(f"{letter}. {drug}" for letter, drug in zip(letters, case["options"]))
            + "\n\nAnswer:"
        )
    request_body = {"model": model, "messages": [
        {"role": "system", "content": "Answer the multiple-choice medication safety question with one letter only."},
        {"role": "user", "content": prompt}],
        "temperature": 0, "max_tokens": 128,
        "provider": {"zdr": True, "data_collection": "deny"}}
    if model.startswith("deepseek/"):
        request_body["reasoning"] = {"effort": "none"}
    body = json.dumps(request_body).encode()
    error = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(API, data=body, headers={
                "Authorization": f"Bearer {key}", "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/ZaneLing/PRISMATIC",
                "X-Title": "PRISMATIC public RxSafeBench pilot"}, method="POST")
            with urllib.request.urlopen(req, timeout=60) as response:
                payload = json.load(response)
            content = payload.get("choices", [{}])[0].get("message", {}).get("content") or ""
            match = re.search(r"\b([%s])\b" % letters, content.strip(), re.I)
            prediction = match.group(1).upper() if match else None
            usage = payload.get("usage") or {}
            return {"case_id": case["id"], "type": case["type"], "gold": case["gold"],
                    "prediction": prediction, "response_valid": prediction is not None,
                    "prompt_tokens": usage.get("prompt_tokens"),
                    "completion_tokens": usage.get("completion_tokens"),
                    "cost_usd": usage.get("cost"), "model_returned": payload.get("model")}
        except urllib.error.HTTPError as exc:
            error = f"HTTP_{exc.code}"
            if exc.code in (400, 401, 402, 403, 404):
                break
        except (urllib.error.URLError, OSError, ValueError, KeyError, IndexError) as exc:
            error = type(exc).__name__
        time.sleep(min(2 ** attempt, 8))
    return {"case_id": case["id"], "type": case["type"], "gold": case["gold"],
            "prediction": None, "response_valid": False, "error": error}


def run(data_dir: Path, output: Path, models: list[str], per_type: int, workers: int) -> dict:
    verify_public_files(data_dir)
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("Set OPENROUTER_API_KEY in the process environment")
    cases = load_cases(data_dir, per_type)
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(output.stem + "_partial.json")
    raw = json.loads(partial.read_text()) if partial.exists() else {}
    for model in models:
        selected_ids = {case["id"] for case in cases}
        prior = raw.get(model, [])
        if any(r["case_id"] not in selected_ids for r in prior):
            raise ValueError("Partial results were produced with a different sample")
        existing = {r["case_id"]: r for r in prior if "error" not in r}
        with ThreadPoolExecutor(max_workers=workers) as pool:
            tasks = {pool.submit(query, model, case, key): case for case in cases
                     if case["id"] not in existing}
            for future in as_completed(tasks):
                record = future.result()
                existing[record["case_id"]] = record
                raw[model] = list(existing.values())
                partial.write_text(json.dumps(raw, ensure_ascii=False) + "\n")
        raw[model] = sorted(existing.values(), key=lambda r: r["case_id"])
    scores = {}
    for model, records in raw.items():
        completed = [r for r in records if "error" not in r]
        exact = [r for r in completed if r["prediction"] == r["gold"]]
        scores[model] = {
            "attempted": len(records), "completed": len(completed),
            "valid_letter": sum(r["response_valid"] for r in completed),
            "correct": len(exact),
            "accuracy_completed": round(len(exact) / len(completed), 5) if completed else None,
            "accuracy_attempted": round(len(exact) / len(records), 5),
            "accuracy_by_type": {kind: round(sum(r["prediction"] == r["gold"] for r in completed
                                                  if r["type"] == kind) /
                                            max(1, sum(r["type"] == kind for r in completed)), 5)
                                 for kind in ("contraindication", "interaction")},
            "prompt_tokens": sum(r.get("prompt_tokens") or 0 for r in completed),
            "completion_tokens": sum(r.get("completion_tokens") or 0 for r in completed),
            "reported_cost_usd": round(sum(float(r.get("cost_usd") or 0) for r in completed), 6),
            "errors": {e: sum(r.get("error") == e for r in records)
                       for e in sorted({r.get("error") for r in records if r.get("error")})},
        }
    report = {
        "benchmark": "RxSafeBench public simulated three-choice medication safety scenarios",
        "source": "https://github.com/CAS-SIAT-XinHai/RxSafeBench",
        "source_commit": SOURCE_COMMIT,
        "sample": "deduplicate by dialogue plus correct drug, then first N sha256-sorted cases per type, fixed option rotation A/B/C",
        "cases": len(cases), "cases_per_type": per_type,
        "gold_option_counts": {letter: sum(c["gold"] == letter for c in cases) for letter in "ABC"},
        "safe_drug_name_in_dialogue_count": sum(c["safe_name_in_dialogue"] for c in cases),
        "routing": {"zdr": True, "data_collection": "deny"},
        "generation": {"temperature": 0, "max_tokens": 128,
                       "deepseek_reasoning_effort": "none"},
        "model_results": scores,
        "limitations": [("full deduplicated public set; scoring protocol differs from published leaderboard"
                         if len(cases) == 2000 else "selected deterministic pilot; not comparable to full-paper leaderboard"),
                        "benchmark gold answers are generated/filtered rather than patient outcomes",
                        "potential answer cue when safe medication name appears in dialogue"],
    }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    # Public benchmark predictions are useful for error review, but no prompt text is retained.
    output.with_name(output.stem + "_predictions.json").write_text(
        json.dumps(raw, ensure_ascii=False, indent=2) + "\n")
    partial.unlink(missing_ok=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True,
                        help="Local checkout of the PUBLIC RxSafeBench/data directory only")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "results/openrouter_rxsafe_pilot.json")
    parser.add_argument("--models", nargs="+", default=list(MODELS))
    parser.add_argument("--per-type", type=int, default=30)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    print(json.dumps(run(args.data_dir, args.output, args.models,
                         args.per_type, args.workers), ensure_ascii=False, indent=2))
