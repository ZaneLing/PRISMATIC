"""Run fixed local MLX weights on a tiny research-only medication-code task.

No network API is called during inference. Prompts and predictions remain in
the restricted data directory. This measures historical agreement, not safety.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import time

from mlx_lm import generate, load
from mlx_lm.sample_utils import make_sampler
from paths import ARTIFACT_DIR, PROJECT_DIR


LOCAL = ARTIFACT_DIR
MODEL = PROJECT_DIR / ".local/models/qwen3-4b-instruct-2507-4bit"
REVISION = "50d427756c6b1b2fe0c0a10f67fbda1fc8e82c1b"


def extract_codes(response: str, allowed: set[str]) -> tuple[list[str], bool]:
    match = re.search(r"\{.*?\}", response, re.DOTALL)
    if not match:
        return [], False
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return [], False
    codes = parsed.get("codes", [])
    if not isinstance(codes, list):
        return [], False
    valid = all(isinstance(code, str) and code in allowed for code in codes)
    valid = valid and len(codes) <= 5 and len(set(codes)) == len(codes)
    return (codes if valid else []), valid


def main() -> dict:
    if not (MODEL / "model.safetensors").exists():
        raise FileNotFoundError("Local model weights are not downloaded")
    cases = [json.loads(line) for line in (LOCAL / "llm_pilot_cases.jsonl").read_text().splitlines()]
    model, tokenizer = load(str(MODEL))
    records = []
    started = time.monotonic()
    for case in cases:
        candidates = "\n".join(f'{item["code"]}: {item["name"]}' for item in case["candidates"])
        messages = [
            {"role": "system", "content": (
                "You are in an offline research experiment that predicts historical medication codes. "
                "This is not for patient care. Select at most five candidate GSN codes using only "
                "the given information. Reply only with JSON in this exact shape: "
                '{"codes":["000000","000001"]}. Do not invent codes.'
            )},
            {"role": "user", "content": (
                f'Chief complaint: {case["chiefcomplaint"]}\n'
                f'Acuity: {case["acuity"]}\n'
                f'Home medications known at admission: {case["home_meds"]}\n'
                f'Allowed codes and names:\n{candidates}'
            )},
        ]
        prompt = tokenizer.apply_chat_template(messages, add_generation_prompt=True,
                                               tokenize=False)
        response = generate(model, tokenizer, prompt=prompt, max_tokens=128,
                            sampler=make_sampler(temp=0.0), verbose=False)
        allowed = {item["code"] for item in case["candidates"]}
        codes, valid = extract_codes(response, allowed)
        records.append({"valid": valid, "predicted_codes": codes,
                        "truth_codes": case["truth_codes"], "raw_response": response})
    with (LOCAL / "llm_pilot_predictions.jsonl").open("w") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    hits = [len(set(r["predicted_codes"]) & set(r["truth_codes"])) for r in records]
    truth_sizes = [len(r["truth_codes"]) for r in records]
    result = {
        "model": "mlx-community/Qwen3-4B-Instruct-2507-4bit",
        "revision": REVISION,
        "task": "local historical code-selection smoke test; no safety or efficacy inference",
        "n_cases": len(records),
        "valid_structured_output_rate": round(sum(r["valid"] for r in records) / len(records), 4),
        "mean_codes_returned": round(sum(len(r["predicted_codes"]) for r in records) / len(records), 3),
        "precision_at_5_budget": round(sum(hits) / (5 * len(records)), 4),
        "micro_recall_at_5_all_targets": round(sum(hits) / sum(truth_sizes), 4),
        "macro_recall_at_5_all_targets": round(sum(h / n for h, n in zip(hits, truth_sizes)) / len(records), 4),
        "elapsed_seconds": round(time.monotonic() - started, 1),
    }
    (LOCAL / "llm_pilot_results.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
