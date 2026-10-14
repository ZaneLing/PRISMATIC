"""Same-case ATC-L4 method pilot; restricted predictions never leave local disk."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.multiclass import OneVsRestClassifier

from build_atc4_cohort import V3


def text_features(frame: pd.DataFrame) -> list[str]:
    return ("chief complaint " + frame.chiefcomplaint.fillna("").astype(str).str.lower()
            + " acuity " + frame.acuity.fillna("unknown").astype(str)
            + " home medicines " + frame.home_meds.fillna("").astype(str).str.lower()).tolist()


def take(frame: pd.DataFrame, split: str, cap: int) -> pd.DataFrame:
    # Sorted IDs make subsampling deterministic without exposing IDs in reports.
    part = frame.loc[frame.split.eq(split)].sort_values("hadm_id")
    if len(part) > cap:
        import hashlib
        ranks = part.hadm_id.map(lambda x: int.from_bytes(
            hashlib.blake2b(f"sample-2026:{x}".encode(), digest_size=8).digest(), "big"))
        part = part.iloc[np.argsort(ranks.to_numpy())[:cap]]
    return part.reset_index(drop=True)


def score(truth: list[set[str]], pred: np.ndarray, classes: list[str]) -> dict:
    hits = np.array([sum(classes[j] in gold for j in row) for gold, row in zip(truth, pred)], dtype=float)
    size = np.array([len(gold) for gold in truth], dtype=float)
    k = pred.shape[1]
    p = float(hits.sum() / (len(truth) * k))
    r = float(hits.sum() / size.sum()) if size.sum() else 0.0
    nonempty = size > 0
    return {
        "precision_at_5": round(p, 5),
        "micro_recall_at_5": round(r, 5),
        "macro_recall_at_5_nonempty": round(float(np.mean(hits[nonempty] / size[nonempty])), 5),
        "micro_f1_at_5": round(2 * p * r / (p + r), 5) if p + r else 0.0,
        "hit_rate_at_5": round(float(np.mean(hits > 0)), 5),
    }


def retrieve_vote(x_query, x_train, y_train: np.ndarray, neighbors: int, k: int) -> np.ndarray:
    result = np.empty((x_query.shape[0], k), dtype=np.int64)
    for lo in range(0, x_query.shape[0], 64):
        hi = min(lo + 64, x_query.shape[0])
        similarities = (x_query[lo:hi] @ x_train.T).toarray()
        idx = np.argpartition(-similarities, neighbors - 1, axis=1)[:, :neighbors]
        weights = np.take_along_axis(similarities, idx, axis=1)
        # Similarity-weighted case voting; zero-score ties use fixed class ordering.
        for row in range(hi - lo):
            votes = np.einsum("n,nc->c", weights[row].astype(np.float64),
                              y_train[idx[row]].astype(np.float64), optimize=False)
            result[lo + row] = np.argsort(-votes, kind="stable")[:k]
    return result


def paired_f1_delta_ci(frame: pd.DataFrame, truth: list[set[str]],
                       first: np.ndarray, second: np.ndarray,
                       classes: list[str], draws: int = 2000) -> dict:
    # Patient clusters, rather than admissions, are the sampling unit.
    group = defaultdict(list)
    for i, sid in enumerate(frame.subject_id):
        group[str(sid)].append(i)
    stats = []
    for indices in group.values():
        targets = sum(len(truth[i]) for i in indices)
        a = sum(sum(classes[j] in truth[i] for j in first[i]) for i in indices)
        b = sum(sum(classes[j] in truth[i] for j in second[i]) for i in indices)
        stats.append((a, b, targets, len(indices) * first.shape[1]))
    values = np.asarray(stats, dtype=np.float64)
    rng = np.random.default_rng(20261014)
    deltas = []
    for _ in range(draws):
        totals = values[rng.integers(0, len(values), len(values))].sum(axis=0)
        denom = totals[2] + totals[3]
        deltas.append(2 * (totals[1] - totals[0]) / denom)
    whole = values.sum(axis=0)
    return {"delta_second_minus_first": round(float(2 * (whole[1] - whole[0]) /
                                                     (whole[2] + whole[3])), 5),
            "patient_bootstrap_95pct": [round(float(x), 5)
                                         for x in np.quantile(deltas, [0.025, 0.975])],
            "patients": len(values), "draws": draws}


def run(cohort: Path, out: Path, train_cap: int, val_cap: int, test_cap: int,
        n_labels: int, k: int, neighbors: int) -> dict:
    frame = pd.read_parquet(cohort)
    parts = {s: take(frame, s, c) for s, c in
             [("train", train_cap), ("val", val_cap), ("test", test_cap)]}
    sets = {s: set(p.subject_id) for s, p in parts.items()}
    assert not (sets["train"] & sets["val"] or sets["train"] & sets["test"] or sets["val"] & sets["test"])
    truth = {s: [set(row) for row in p.atc4_codes] for s, p in parts.items()}
    freq = Counter(code for row in truth["train"] for code in row)
    classes = [code for code, _ in freq.most_common(n_labels)]
    class_index = {v: i for i, v in enumerate(classes)}
    y_train = np.zeros((len(parts["train"]), len(classes)), dtype=np.float32)
    for i, row in enumerate(truth["train"]):
        for code in row:
            if code in class_index:
                y_train[i, class_index[code]] = 1

    vectorizer = TfidfVectorizer(min_df=3, max_features=12000,
                                 ngram_range=(1, 2), token_pattern=r"(?u)\b\w+\b",
                                 sublinear_tf=True)
    x_train = vectorizer.fit_transform(text_features(parts["train"]))
    x_val = vectorizer.transform(text_features(parts["val"]))
    x_test = vectorizer.transform(text_features(parts["test"]))

    popularity = np.tile(np.arange(k), (len(parts["test"]), 1))
    retrieval = retrieve_vote(x_test, x_train, y_train, neighbors, k)
    model = OneVsRestClassifier(SGDClassifier(loss="log_loss", alpha=1e-5,
                                              max_iter=50, tol=1e-3, random_state=42), n_jobs=1)
    model.fit(x_train, y_train)
    direct = np.argsort(-model.predict_proba(x_test), axis=1, kind="stable")[:, :k]
    direct_val = np.argsort(-model.predict_proba(x_val), axis=1, kind="stable")[:, :k]
    retrieval_val = retrieve_vote(x_val, x_train, y_train, neighbors, k)
    report = {
        "task": "MIMIC-IV/ED historical 6h all-route ATC-L4 order-set prediction; not clinical correctness",
        "population": "all eligible ED-to-hospital admissions; no future-order inclusion rule",
        "method_comparison_status": "pilot: three locally executed methods; paper architectures and full harness pending",
        "split": "patient disjoint, same fixed test cases for every row",
        "sampled_admissions": {s: len(p) for s, p in parts.items()},
        "sampled_patients": {s: len(sets[s]) for s in sets},
        "label_space": f"top {len(classes)} ATC-L4 codes by training prevalence only",
        "prediction_budget": f"exactly {k} ATC-L4 codes per case",
        "case_retrieval_neighbors": neighbors,
        "label_coverage_in_test": round(sum(len(row & class_index.keys()) for row in truth["test"])
                                        / sum(map(len, truth["test"])), 5),
        "test_cases_with_no_mapped_label": sum(not row for row in truth["test"]),
        "metrics_test": {
            "train_prevalence": score(truth["test"], popularity, classes),
            "case_retrieval": score(truth["test"], retrieval, classes),
            "direct_tfidf_sgd": score(truth["test"], direct, classes),
        },
        "metrics_validation": {
            "case_retrieval": score(truth["val"], retrieval_val, classes),
            "direct_tfidf_sgd": score(truth["val"], direct_val, classes),
        },
        "paired_test_micro_f1": {
            "direct_minus_retrieval": paired_f1_delta_ci(
                parts["test"], truth["test"], retrieval, direct, classes),
            "retrieval_minus_prevalence": paired_f1_delta_ci(
                parts["test"], truth["test"], popularity, retrieval, classes),
        },
        "disclosures": ["ATC-L4 NDC mapping incomplete; see atc4_mapping_audit.json",
                        "all metrics compare historical orders rather than appropriateness or safety",
                        "no post-decision diagnosis, procedures, labs, or prescriptions used as input"],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort", type=Path, default=V3 / "cohort_atc4_6h.parquet")
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "results/atc4_method_pilot.json")
    ap.add_argument("--train", type=int, default=40000)
    ap.add_argument("--val", type=int, default=4000)
    ap.add_argument("--test", type=int, default=4000)
    ap.add_argument("--labels", type=int, default=80)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--neighbors", type=int, default=30)
    a = ap.parse_args()
    print(json.dumps(run(a.cohort, a.out, a.train, a.val, a.test, a.labels, a.k, a.neighbors),
                     ensure_ascii=False, indent=2))
