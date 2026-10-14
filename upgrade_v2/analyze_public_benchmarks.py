"""Paired uncertainty for public benchmark pilots; invalid/API failures count wrong."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from run_rxqa_openrouter import wilson


def analyze(path: Path, draws: int = 5000) -> dict:
    data = json.loads(path.read_text())
    models = list(data)
    maps = {model: {r["case_id"]: int(r.get("prediction") == r["gold"])
                    for r in rows} for model, rows in data.items()}
    ids = sorted(set.intersection(*(set(v) for v in maps.values())))
    if not ids:
        raise ValueError("No matched questions")
    scores = {m: np.array([maps[m][i] for i in ids], dtype=float) for m in models}
    result = {"matched_questions": len(ids), "models": {}, "paired_deltas": {}}
    for model, values in scores.items():
        result["models"][model] = {
            "correct": int(values.sum()), "accuracy": round(float(values.mean()), 5),
            "wilson_95pct": wilson(int(values.sum()), len(ids)),
        }
    rng = np.random.default_rng(20261014)
    sample = rng.integers(0, len(ids), size=(draws, len(ids)))
    for i, a in enumerate(models):
        for b in models[i + 1:]:
            delta = scores[a] - scores[b]
            draws_delta = delta[sample].mean(axis=1)
            result["paired_deltas"][f"{a} minus {b}"] = {
                "accuracy_difference": round(float(delta.mean()), 5),
                "bootstrap_95pct": [round(float(x), 5) for x in np.quantile(draws_delta, [0.025, 0.975])],
                "discordant_a_only": int(((scores[a] == 1) & (scores[b] == 0)).sum()),
                "discordant_b_only": int(((scores[a] == 0) & (scores[b] == 1)).sum()),
            }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rxsafe", type=Path,
                        default=Path(__file__).parent / "results/openrouter_rxsafe_pilot_predictions.json")
    parser.add_argument("--rxqa", type=Path,
                        default=Path(__file__).parent / "results/openrouter_rxqa_pilot_predictions.json")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).parent / "results/public_paired_comparison.json")
    args = parser.parse_args()
    out = {"RxSafeBench": analyze(args.rxsafe), "RxQA_OpenFDA": analyze(args.rxqa)}
    args.output.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
