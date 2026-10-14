"""Prepare a small local-only LLM pilot from held-out admissions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import joblib
import pandas as pd

from train_baselines import LOCAL_DIR, sampled_indices, stable_bucket
from paths import RESTRICTED_ROOT


def main(cohort_path: Path, restricted: Path, n: int) -> dict:
    frame = pd.read_parquet(cohort_path)
    frame["split"] = frame["subject_id"].map(
        lambda x: "test" if stable_bucket(x, "patient-split-2026") % 10 == 0 else "other")
    frame = frame.iloc[sampled_indices(frame, "test", n)].reset_index(drop=True)
    classes = joblib.load(LOCAL_DIR / "tfidf_sgd_chief_home.joblib")["classes"]
    path = restricted / "mimiciv/3.1/hosp/prescriptions.csv.gz"
    con = duckdb.connect()
    placeholders = ",".join("?" for _ in classes)
    rows = con.execute(f"""
        SELECT gsn, MODE(drug) AS common_name
        FROM read_csv('{str(path).replace("'", "''")}', all_varchar=true)
        WHERE gsn IN ({placeholders})
        GROUP BY gsn
    """, classes).fetchall()
    names = dict(rows)
    candidate_list = [{"code": code, "name": names.get(code, "unknown")}
                      for code in classes]
    out = LOCAL_DIR / "llm_pilot_cases.jsonl"
    with out.open("w") as f:
        for _, row in frame.iterrows():
            case = {
                "chiefcomplaint": row["chiefcomplaint"] if pd.notna(row["chiefcomplaint"]) else "",
                "acuity": row["acuity"] if pd.notna(row["acuity"]) else "",
                "home_meds": row["home_meds"] if pd.notna(row["home_meds"]) else "",
                "truth_codes": list(row["target_codes"]),
                "candidates": candidate_list,
            }
            f.write(json.dumps(case, ensure_ascii=False) + "\n")
    con.close()
    return {"pilot_cases": len(frame), "candidate_codes": len(classes),
            "patient_level_file": "local only under restricted/prismatic-v2/llm_pilot_cases.jsonl"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", type=Path, default=LOCAL_DIR / "cohort_6h.parquet")
    parser.add_argument("--restricted", type=Path, default=RESTRICTED_ROOT)
    parser.add_argument("--n", type=int, default=32)
    args = parser.parse_args()
    print(json.dumps(main(args.cohort, args.restricted, args.n), indent=2))
