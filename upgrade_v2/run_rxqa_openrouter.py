"""OpenRouter pilot on the public pharmacist-reviewed RxQA OpenFDA subset."""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import hashlib
import json
import math
import os
from pathlib import Path

from run_public_openrouter import MODELS, query


SOURCE_COMMIT = "203979bf928c1fe9e45aa89e2ed76c3d2a63b503"
PUBLIC_SHA256 = "52f99903426296c5576757aacaa500200616ecb501fb5d2b9d2c287ddfef8853"


def verify_public_file(path: Path) -> None:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != PUBLIC_SHA256:
        raise ValueError("RxQA public benchmark checksum mismatch")


def wilson(correct: int, n: int) -> list[float] | None:
    if not n:
        return None
    z = 1.959963984540054
    p = correct / n
    a = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / a
    span = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / a
    return [round(mid - span, 5), round(mid + span, 5)]


def load_cases(path: Path, count: int) -> list[dict]:
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 300:
        raise ValueError(f"Expected 300 public RxQA OpenFDA questions; found {len(rows)}")
    chosen = sorted(rows, key=lambda row: hashlib.sha256(row["q_id"].encode()).hexdigest())[:count]
    cases = []
    for row in chosen:
        gold = "ABCD"[int(row["correct_idx"])]
        if row[gold] != row["correct"]:
            raise ValueError(f"Gold mismatch at q_id={row['q_id']}")
        cases.append({"id": row["q_id"], "type": "rxqa_openfda",
                      "difficulty": row["pharmacist_rated_difficulty"],
                      "question": row["question"],
                      "options": [row[k] for k in "ABCD"], "gold": gold})
    return cases


def run(path: Path, output: Path, count: int, models: list[str], workers: int) -> dict:
    verify_public_file(path)
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("Set OPENROUTER_API_KEY in the process environment")
    cases = load_cases(path, count)
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(output.stem + "_partial.json")
    raw = json.loads(partial.read_text()) if partial.exists() else {}
    scores = {}
    for model in models:
        selected_ids = {case["id"] for case in cases}
        prior = raw.get(model, [])
        if any(r["case_id"] not in selected_ids for r in prior):
            raise ValueError("Partial results were produced with a different sample")
        existing = {r["case_id"]: r for r in prior if "error" not in r}
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(query, model, case, key): case for case in cases
                       if case["id"] not in existing}
            for future in as_completed(futures):
                record = future.result()
                existing[record["case_id"]] = record
                raw[model] = list(existing.values())
                partial.write_text(json.dumps(raw, ensure_ascii=False) + "\n")
        records = list(existing.values())
        raw[model] = sorted(records, key=lambda r: int(r["case_id"]))
        completed = [r for r in records if "error" not in r]
        correct = sum(r["prediction"] == r["gold"] for r in completed)
        scores[model] = {
            "attempted": len(records), "completed": len(completed),
            "valid_letter": sum(r["response_valid"] for r in completed),
            "correct": correct,
            "accuracy_completed": round(correct / len(completed), 5) if completed else None,
            "accuracy_attempted": round(correct / len(records), 5),
            "accuracy_wilson_95pct_completed": wilson(correct, len(completed)),
            "prompt_tokens": sum(r.get("prompt_tokens") or 0 for r in completed),
            "completion_tokens": sum(r.get("completion_tokens") or 0 for r in completed),
            "reported_cost_usd": round(sum(float(r.get("cost_usd") or 0) for r in completed), 6),
            "errors": dict(Counter(r["error"] for r in records if r.get("error"))),
        }
    report = {
        "benchmark": "RxQA OpenFDA four-choice medication reasoning",
        "source": "https://github.com/Google-Health/rxqa",
        "source_commit": SOURCE_COMMIT,
        "population": "public pharmacist-reviewed OpenFDA subset; 300 available questions",
        "sample": "first N sha256-sorted q_id values; original option order",
        "cases": len(cases),
        "gold_option_counts": dict(Counter(c["gold"] for c in cases)),
        "always_most_common_gold_letter_baseline_accuracy": round(
            max(Counter(c["gold"] for c in cases).values()) / len(cases), 5),
        "difficulty_counts": dict(Counter(c["difficulty"] for c in cases)),
        "routing": {"zdr": True, "data_collection": "deny"},
        "generation": {"temperature": 0, "max_tokens": 128,
                       "deepseek_reasoning_effort": "none"},
        "model_results": scores,
        "limitations": ["selected subset, not the full 300-question benchmark",
                        "four-choice knowledge/reasoning is distinct from real prescription construction",
                        "single-pharmacist review per item and selection bias in source benchmark",
                        "original option positions are imbalanced in this sample: 46% of gold answers are C"],
    }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    output.with_name(output.stem + "_predictions.json").write_text(
        json.dumps(raw, ensure_ascii=False, indent=2) + "\n")
    partial.unlink(missing_ok=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "results/openrouter_rxqa_pilot.json")
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--models", nargs="+", default=list(MODELS))
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    print(json.dumps(run(args.csv, args.output, args.count,
                         args.models, args.workers), ensure_ascii=False, indent=2))
