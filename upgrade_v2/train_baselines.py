"""Train local historical-order baselines; emit aggregate metrics only."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.multiclass import OneVsRestClassifier
from sklearn.naive_bayes import MultinomialNB
from paths import ARTIFACT_DIR


LOCAL_DIR = ARTIFACT_DIR


def stable_bucket(value: object, salt: str) -> int:
    digest = hashlib.blake2b(f"{salt}:{value}".encode(), digest_size=8).digest()
    return int.from_bytes(digest, "big")


def sampled_indices(frame: pd.DataFrame, split: str, cap: int) -> np.ndarray:
    mask = frame["split"].eq(split).to_numpy()
    idx = np.flatnonzero(mask)
    if len(idx) <= cap:
        return idx
    scores = np.fromiter(
        (stable_bucket(v, "sample-2026") for v in frame.iloc[idx]["hadm_id"]),
        dtype=np.uint64,
        count=len(idx),
    )
    return idx[np.argsort(scores)[:cap]]


def make_text(frame: pd.DataFrame, include_home: bool) -> list[str]:
    chief = frame["chiefcomplaint"].fillna("").astype(str).str.lower()
    acuity = frame["acuity"].fillna("unknown").astype(str)
    result = ("chief complaint " + chief + " acuity " + acuity).tolist()
    if include_home:
        homes = frame["home_meds"].fillna("").astype(str).str.lower().tolist()
        result = [a + " home medications " + b for a, b in zip(result, homes)]
    return result


def target_lists(frame: pd.DataFrame) -> list[set[str]]:
    return [set(x) for x in frame["target_codes"]]


def metrics_at_k(truth: list[set[str]], predictions: np.ndarray, classes: list[str]) -> dict:
    hits = np.zeros(len(truth), dtype=float)
    sizes = np.fromiter((len(t) for t in truth), dtype=float, count=len(truth))
    for i, true in enumerate(truth):
        hits[i] = sum(classes[j] in true for j in predictions[i])
    k = predictions.shape[1]
    micro_precision = float(hits.sum() / (len(truth) * k))
    micro_recall = float(hits.sum() / sizes.sum())
    return {
        "precision_at_k": round(micro_precision, 5),
        "micro_recall_at_k_all_targets": round(micro_recall, 5),
        "macro_recall_at_k_all_targets": round(float(np.mean(hits / sizes)), 5),
        "hit_rate_at_k": round(float(np.mean(hits > 0)), 5),
        "micro_f1_at_k": round(2 * micro_precision * micro_recall / (micro_precision + micro_recall), 5)
        if micro_precision + micro_recall else 0.0,
    }


def patient_bootstrap_delta(
    frame: pd.DataFrame, truth: list[set[str]], baseline: np.ndarray,
    candidate: np.ndarray, classes: list[str], draws: int = 200,
) -> list[float]:
    # Paired resampling by patient keeps repeat admissions together.
    by_patient: dict[str, list[int]] = defaultdict(list)
    for i, sid in enumerate(frame["subject_id"].astype(str)):
        by_patient[sid].append(i)
    patients = np.array(list(by_patient))
    base_case = np.array([sum(classes[j] in t for j in baseline[i]) / len(t) for i, t in enumerate(truth)])
    cand_case = np.array([sum(classes[j] in t for j in candidate[i]) / len(t) for i, t in enumerate(truth)])
    delta = cand_case - base_case
    rng = np.random.default_rng(20261014)
    values = []
    for _ in range(draws):
        chosen = rng.choice(patients, size=len(patients), replace=True)
        indices = [i for p in chosen for i in by_patient[p]]
        values.append(float(np.mean(delta[indices])))
    return [round(float(x), 5) for x in np.quantile(values, [0.025, 0.975])]


def run(cohort_path: Path, output_dir: Path, max_train: int, max_val: int,
        max_test: int, n_labels: int, k: int) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.read_parquet(cohort_path)
    frame["split"] = frame["subject_id"].map(
        lambda x: "test" if stable_bucket(x, "patient-split-2026") % 10 == 0
        else ("val" if stable_bucket(x, "patient-split-2026") % 10 == 1 else "train")
    )
    selected = {
        "train": sampled_indices(frame, "train", max_train),
        "val": sampled_indices(frame, "val", max_val),
        "test": sampled_indices(frame, "test", max_test),
    }
    parts = {name: frame.iloc[idx].reset_index(drop=True) for name, idx in selected.items()}
    patient_sets = {name: set(part["subject_id"]) for name, part in parts.items()}
    assert not (patient_sets["train"] & patient_sets["val"])
    assert not (patient_sets["train"] & patient_sets["test"])
    assert not (patient_sets["val"] & patient_sets["test"])

    truth = {name: target_lists(part) for name, part in parts.items()}
    frequency = Counter(code for codes in truth["train"] for code in codes)
    classes = [code for code, _ in frequency.most_common(n_labels)]
    class_to_index = {v: i for i, v in enumerate(classes)}
    y_train = np.zeros((len(parts["train"]), len(classes)), dtype=np.uint8)
    for row, codes in enumerate(truth["train"]):
        for code in codes:
            if code in class_to_index:
                y_train[row, class_to_index[code]] = 1

    popularity = np.tile(np.arange(k), (len(parts["test"]), 1))
    popularity_val = np.tile(np.arange(k), (len(parts["val"]), 1))
    results = {"popularity": metrics_at_k(truth["test"], popularity, classes)}
    validation = {"popularity": metrics_at_k(truth["val"], popularity_val, classes)}
    saved_models = []
    for name, include_home, estimator in [
        ("tfidf_nb_chief", False, MultinomialNB(alpha=1.0)),
        ("tfidf_nb_chief_home", True, MultinomialNB(alpha=1.0)),
        ("tfidf_sgd_chief_home", True, SGDClassifier(loss="log_loss", alpha=1e-5,
                                                     max_iter=50, tol=1e-3, random_state=42)),
    ]:
        vectorizer = TfidfVectorizer(min_df=3, max_features=12000, ngram_range=(1, 2),
                                     token_pattern=r"(?u)\b\w+\b", sublinear_tf=True)
        x_train = vectorizer.fit_transform(make_text(parts["train"], include_home))
        x_val = vectorizer.transform(make_text(parts["val"], include_home))
        x_test = vectorizer.transform(make_text(parts["test"], include_home))
        model = OneVsRestClassifier(estimator, n_jobs=1)
        model.fit(x_train, y_train)
        val_scores = model.predict_proba(x_val)
        pred_val = np.argsort(-val_scores, axis=1)[:, :k]
        validation[name] = metrics_at_k(truth["val"], pred_val, classes)
        scores = model.predict_proba(x_test)
        pred = np.argsort(-scores, axis=1)[:, :k]
        results[name] = metrics_at_k(truth["test"], pred, classes)
        results[name]["macro_recall_delta_vs_popularity_95pct_patient_bootstrap"] = patient_bootstrap_delta(
            parts["test"], truth["test"], popularity, pred, classes)
        joblib.dump({"vectorizer": vectorizer, "model": model, "classes": classes},
                    output_dir / f"{name}.joblib", compress=3)
        saved_models.append(name)

    test_truth_count = sum(len(x) for x in truth["test"])
    covered = sum(len(x.intersection(class_to_index)) for x in truth["test"])
    report = {
        "task": "historical oral GSN set prediction; not clinical safety or correctness",
        "split": "patient-disjoint deterministic hash; 80/10/10 before sampling",
        "sampled_admissions": {name: len(part) for name, part in parts.items()},
        "sampled_patients": {name: len(patient_sets[name]) for name in parts},
        "patient_overlap_across_splits": 0,
        "label_space_top_n_from_train_only": len(classes),
        "test_true_label_coverage_by_label_space": round(covered / test_truth_count, 5),
        "predictions_per_case_k": k,
        "validation_models": validation,
        "selected_model_by_validation_macro_recall": max(
            validation, key=lambda name: validation[name]["macro_recall_at_k_all_targets"]),
        "models": results,
        "saved_models_in_restricted_local_dir": saved_models,
    }
    (output_dir / "baseline_results.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", type=Path, default=LOCAL_DIR / "cohort_6h.parquet")
    parser.add_argument("--output-dir", type=Path, default=LOCAL_DIR)
    parser.add_argument("--max-train", type=int, default=40000)
    parser.add_argument("--max-val", type=int, default=4000)
    parser.add_argument("--max-test", type=int, default=4000)
    parser.add_argument("--n-labels", type=int, default=64)
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()
    print(json.dumps(run(args.cohort, args.output_dir, args.max_train,
                         args.max_val, args.max_test, args.n_labels, args.k), indent=2))
