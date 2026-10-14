"""Separate no recorded six-hour orders from orders with no mapped ATC label.

Read restricted inputs locally; publish aggregate counts only. This audit does
not assert that an unrecorded order is clinically unnecessary or that starttime
is the actual time when a clinician authored the order.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path

import duckdb
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "upgrade_v3"))
from run_atc4_methods import take

ROOT = Path.home() / "Desktop/MedTreeBench/dataset/restricted"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cohort: Path, prescriptions: Path, private_dir: Path) -> dict:
    con = duckdb.connect()
    con.execute("SET threads=4")
    con.execute("CREATE TEMP TABLE cohort AS SELECT * FROM read_parquet(?)", [str(cohort)])
    con.execute("""
        CREATE TEMP TABLE raw_counts AS
        SELECT c.hadm_id,
            COUNT(*) FILTER (WHERE TRY_CAST(p.starttime AS TIMESTAMP) >= c.decision_time
                AND TRY_CAST(p.starttime AS TIMESTAMP) < c.decision_time + INTERVAL 6 HOUR) AS raw_orders_6h,
            COUNT(*) FILTER (WHERE TRY_CAST(p.starttime AS TIMESTAMP) IS NULL) AS unparseable_starttime_rows
        FROM read_csv(?, all_varchar=true) p
        JOIN cohort c ON p.hadm_id=c.hadm_id AND p.subject_id=c.subject_id
        GROUP BY c.hadm_id
    """, [str(prescriptions)])
    frame = con.execute("""
        SELECT c.subject_id,c.hadm_id,c.split,LEN(c.atc4_codes) AS mapped_classes,
               COALESCE(r.raw_orders_6h,0) AS raw_orders_6h,
               COALESCE(r.unparseable_starttime_rows,0) AS unparseable_starttime_rows
        FROM cohort c LEFT JOIN raw_counts r USING(hadm_id)
    """).fetchdf()
    assert not ((frame.raw_orders_6h == 0) & (frame.mapped_classes > 0)).any()
    frame["label_status"] = "at_least_one_mapped_class"
    frame.loc[frame.mapped_classes.eq(0), "label_status"] = "orders_present_but_no_mapped_class"
    frame.loc[frame.raw_orders_6h.eq(0), "label_status"] = "no_recorded_order_in_window"
    assert frame.hadm_id.is_unique
    def summarize(part: pd.DataFrame) -> dict:
        counts = {str(k): int(v) for k, v in part.label_status.value_counts().items()}
        return {"admissions": len(part), "patients": int(part.subject_id.nunique()),
                "status_counts": counts, "raw_order_rows_6h": int(part.raw_orders_6h.sum()),
                "mapped_class_instances": int(part.mapped_classes.sum()),
                "admissions_with_unparseable_starttime_rows": int(part.unparseable_starttime_rows.gt(0).sum()),
                "unparseable_starttime_rows_any_time": int(part.unparseable_starttime_rows.sum())}
    scopes = {"all": frame, **{s: frame.loc[frame.split.eq(s)] for s in ("train", "val", "test")}}
    scopes["v03_test_sample_4000"] = take(frame, "test", 4000)
    report = {
        "protocol": "P01a-label-observability-v1",
        "cohort_sha256": sha256(cohort),
        "scope": "MIMIC-IV/ED admission during ED stay; recorded prescriptions starttime in [admission, admission+6h)",
        "scopes": {name: summarize(part) for name, part in scopes.items()},
        "limits": ["No recorded order does not establish no clinical need.",
                   "Partially mapped cases can still contain missing drug classes.",
                   "Medication starttime is not necessarily authoring or availability time.",
                   "Current benchmark encoders use chiefcomplaint, acuity, home_meds only.",
                   "v0.3 hash test results have been inspected; they are developmental evidence.",
                   "Current train-derived mapping used the full training patient pool, beyond the 40000-admission model sample."],
    }
    private_dir.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(private_dir / "label_observability.parquet", index=False)
    con.close()
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--cohort", type=Path, default=ROOT / "prismatic-v3/cohort_atc4_6h.parquet")
    p.add_argument("--prescriptions", type=Path, default=ROOT / "mimiciv/3.1/hosp/prescriptions.csv.gz")
    p.add_argument("--private-dir", type=Path, default=ROOT / "prismatic-v4")
    p.add_argument("--output", type=Path, default=Path(__file__).parent / "results/label_observability_audit.json")
    args = p.parse_args()
    report = run(args.cohort, args.prescriptions, args.private_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
