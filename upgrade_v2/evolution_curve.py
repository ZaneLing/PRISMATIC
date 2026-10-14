"""Prospective-style case-count curve for historical supportive orders.

The case memory grows in fixed, cumulative batches. Test patients never enter
the memory or vectorizer. Metrics are ranking/calibration metrics, not a claim
that historical orders are appropriate for another patient.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from paths import ARTIFACT_DIR
from train_baselines import make_text, sampled_indices, stable_bucket


LABELS = ("saline_iv", "ondansetron", "bowel_regimen")
SIZES = (250, 1000, 4000, 16000, 40000)


def memory_scores(x_test: csr_matrix, x_memory: csr_matrix,
                  y_memory: np.ndarray, prevalence: np.ndarray,
                  neighbors: int = 30, batch: int = 100) -> np.ndarray:
    """Weighted nearest precedent votes with a prevalence prior."""
    result = np.empty((x_test.shape[0], y_memory.shape[1]), dtype=np.float64)
    for start in range(0, x_test.shape[0], batch):
        sim = (x_test[start:start + batch] @ x_memory.T).toarray()
        k = min(neighbors, sim.shape[1])
        indices = np.argpartition(-sim, k - 1, axis=1)[:, :k]
        weights = np.take_along_axis(sim, indices, axis=1)
        # Sparse text can have zero overlap: fall back to the training prior.
        weighted = (y_memory[indices] * weights[:, :, None]).sum(axis=1)
        denom = weights.sum(axis=1, keepdims=True)
        result[start:start + batch] = (weighted + 2 * prevalence) / (denom + 2)
    return result


def score(y_true: np.ndarray, probs: np.ndarray) -> dict:
    out = {}
    for col, label in enumerate(LABELS):
        gold = y_true[:, col]
        p = np.clip(probs[:, col], 0, 1)
        out[label] = {
            "prevalence": round(float(gold.mean()), 5),
            "average_precision": round(float(average_precision_score(gold, p)), 5),
            "auroc": round(float(roc_auc_score(gold, p)), 5) if len(np.unique(gold)) == 2 else None,
            "brier": round(float(brier_score_loss(gold, p)), 5),
        }
    out["macro_average_precision"] = round(float(np.mean([
        out[label]["average_precision"] for label in LABELS])), 5)
    return out


def patient_bootstrap_macro_ap_delta(test: pd.DataFrame, y_true: np.ndarray,
                                     early: np.ndarray, late: np.ndarray,
                                     draws: int = 300) -> list[float]:
    groups = test.groupby("subject_id", sort=False).indices
    patients = list(groups)
    rng = np.random.default_rng(20261014)
    deltas = []
    for _ in range(draws):
        sampled = rng.integers(0, len(patients), size=len(patients))
        indices = np.concatenate([groups[patients[j]] for j in sampled])
        values = []
        for col in range(len(LABELS)):
            gold = y_true[indices, col]
            if len(np.unique(gold)) < 2:
                continue
            values.append(average_precision_score(gold, late[indices, col]) -
                          average_precision_score(gold, early[indices, col]))
        deltas.append(float(np.mean(values)))
    return [round(float(x), 5) for x in np.quantile(deltas, [0.025, 0.975])]


def run(cohort: Path, output: Path, max_test: int = 1000) -> dict:
    frame = pd.read_parquet(cohort, columns=[
        "subject_id", "hadm_id", "chiefcomplaint", "acuity", "home_meds", *LABELS])
    frame["split"] = frame["subject_id"].map(
        lambda x: "test" if stable_bucket(x, "patient-split-2026") % 10 == 0
        else ("val" if stable_bucket(x, "patient-split-2026") % 10 == 1 else "train"))
    train_idx = sampled_indices(frame, "train", max(SIZES))
    test_idx = sampled_indices(frame, "test", max_test)
    train = frame.iloc[train_idx].reset_index(drop=True)
    test = frame.iloc[test_idx].reset_index(drop=True)
    assert set(train.subject_id).isdisjoint(set(test.subject_id))
    y_train = train[list(LABELS)].to_numpy(dtype=np.uint8)
    y_test = test[list(LABELS)].to_numpy(dtype=np.uint8)

    vectorizer = HashingVectorizer(n_features=2**17, alternate_sign=False,
                                   ngram_range=(1, 2), norm="l2",
                                   token_pattern=r"(?u)\b\w+\b")
    x_train = vectorizer.transform(make_text(train, include_home=True)).tocsr()
    x_test = vectorizer.transform(make_text(test, include_home=True)).tocsr()
    # Positive and negative cases are learned separately for every label.
    models = [SGDClassifier(loss="log_loss", alpha=1e-5, random_state=2026 + i,
                            learning_rate="optimal") for i in range(len(LABELS))]
    curves = []
    saved_predictions = {}
    previous = 0
    for n in SIZES:
        if n > len(train):
            break
        for col, model in enumerate(models):
            model.partial_fit(x_train[previous:n], y_train[previous:n, col], classes=np.array([0, 1]))
        previous = n
        prior = y_train[:n].mean(axis=0)
        base = np.broadcast_to(prior, (len(test), len(LABELS)))
        knn = memory_scores(x_test, x_train[:n], y_train[:n], prior)
        online = np.column_stack([m.predict_proba(x_test)[:, 1] for m in models])
        curves.append({
            "cases_seen": n,
            "positive_train_cases": dict(zip(LABELS, y_train[:n].sum(axis=0).astype(int).tolist())),
            "prevalence_baseline": score(y_test, base),
            "case_memory_knn30": score(y_test, knn),
            "incremental_sgd": score(y_test, online),
        })
        if n in (SIZES[0], SIZES[-1]):
            saved_predictions[n] = {"memory": knn, "online": online}
    improvement_ci = {}
    if SIZES[0] in saved_predictions and SIZES[-1] in saved_predictions:
        for name in ("memory", "online"):
            improvement_ci[name] = patient_bootstrap_macro_ap_delta(
                test, y_test, saved_predictions[SIZES[0]][name],
                saved_predictions[SIZES[-1]][name])
    report = {
        "task": "historical supportive-order prediction (saline IV, ondansetron, bowel regimen)",
        "split": "patient-disjoint deterministic 80/10/10 hash; cumulative train prefixes; fixed test sample",
        "training_cases_available": len(train), "test_cases": len(test),
        "train_test_patient_overlap": 0,
        "features": "pre-decision ED chief complaint, acuity, home medication reconciliation",
        "case_memory": "top-30 cosine-similar prior cases with weighted votes and a two-observation prevalence prior",
        "online_model": "per-label SGD logistic loss, cumulative partial_fit without test feedback",
        "limitation": "historical clinician order matching, not medical appropriateness or safety; pilot conditioned on an oral order",
        "macro_ap_delta_40000_minus_250_95pct_patient_bootstrap": improvement_ci,
        "curves": curves,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", type=Path, default=ARTIFACT_DIR / "supportive_cohort_6h.parquet")
    parser.add_argument("--output", type=Path, default=ARTIFACT_DIR / "evolution_curve.json")
    parser.add_argument("--max-test", type=int, default=1000)
    args = parser.parse_args()
    result = run(args.cohort, args.output, args.max_test)
    print(json.dumps({"test_cases": result["test_cases"],
                      "curves": [{"cases_seen": row["cases_seen"],
                                  "memory_macro_ap": row["case_memory_knn30"]["macro_average_precision"],
                                  "online_macro_ap": row["incremental_sgd"]["macro_average_precision"]}
                                 for row in result["curves"]]}, indent=2))
