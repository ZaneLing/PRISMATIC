"""Compare local LLM smoke test with the saved baseline on identical cases."""

import json

import joblib
import numpy as np

from train_baselines import LOCAL_DIR, metrics_at_k


def main() -> dict:
    cases = [json.loads(line) for line in (LOCAL_DIR / "llm_pilot_cases.jsonl").read_text().splitlines()]
    llm = [json.loads(line) for line in (LOCAL_DIR / "llm_pilot_predictions.jsonl").read_text().splitlines()]
    if len(cases) != len(llm):
        raise ValueError("pilot case/prediction count mismatch")
    truth = [set(c["truth_codes"]) for c in cases]
    bundle = joblib.load(LOCAL_DIR / "tfidf_sgd_chief_home.joblib")
    classes = bundle["classes"]
    texts = ["chief complaint " + str(c["chiefcomplaint"]).lower() +
             " acuity " + str(c["acuity"]) +
             " home medications " + str(c["home_meds"]).lower() for c in cases]
    scores = bundle["model"].predict_proba(bundle["vectorizer"].transform(texts))
    pred_sgd = np.argsort(-scores, axis=1)[:, :5]
    pred_pop = np.tile(np.arange(5), (len(cases), 1))
    report = {
        "n_cases": len(cases),
        "task": "tiny local smoke test on identical held-out cases; exploratory only",
        "popularity": metrics_at_k(truth, pred_pop, classes),
        "tfidf_sgd_chief_home": metrics_at_k(truth, pred_sgd, classes),
        "llm": json.loads((LOCAL_DIR / "llm_pilot_results.json").read_text()),
    }
    (LOCAL_DIR / "llm_pilot_comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
