"""Audit timestamp observability without publishing any patient-level values."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

import duckdb

ROOT = Path.home() / "Desktop/MedTreeBench/dataset/restricted"
SOURCES = {
    "triage": "mimic-iv-ed-v2.2/ed/triage.csv.gz",
    "medrecon": "mimic-iv-ed-v2.2/ed/medrecon.csv.gz",
    "vitalsign": "mimic-iv-ed-v2.2/ed/vitalsign.csv.gz",
    "labevents": "mimiciv/3.1/hosp/labevents.csv.gz",
    "prescriptions": "mimiciv/3.1/hosp/prescriptions.csv.gz",
}


def audit(root: Path, cohort: Path) -> dict:
    headers = {}
    for name, relative in SOURCES.items():
        with gzip.open(root / relative, "rt") as stream:
            columns = next(csv.reader(stream))
        headers[name] = {
            "columns": columns,
            "timestamp_columns": [c for c in columns if "time" in c.lower()],
        }
    expected = {"triage": [], "medrecon": ["charttime"], "vitalsign": ["charttime"],
                "labevents": ["charttime", "storetime"], "prescriptions": ["starttime", "stoptime"]}
    for name, columns in expected.items():
        if set(headers[name]["timestamp_columns"]) != set(columns):
            raise ValueError(f"Timestamp schema changed for {name}; review conclusions before publishing")
    con = duckdb.connect()
    con.execute("CREATE TEMP TABLE cohort AS SELECT * FROM read_parquet(?)", [str(cohort)])
    row = con.execute("""
        SELECT COUNT(*) AS admissions,
            COUNT(*) FILTER (WHERE decision_time IS NULL) AS missing_decision_time,
            COUNT(*) FILTER (WHERE max_home_med_charttime > decision_time) AS home_med_charttime_after_decision,
            COUNT(*) FILTER (WHERE home_med_count > 0 AND max_home_med_charttime IS NULL) AS home_med_missing_charttime,
            COUNT(*) FILTER (WHERE home_med_count > 0) AS admissions_with_home_meds,
            COUNT(*) FILTER (WHERE chiefcomplaint IS NOT NULL AND TRIM(chiefcomplaint) <> '') AS admissions_with_chiefcomplaint,
            COUNT(*) FILTER (WHERE acuity IS NOT NULL) AS admissions_with_acuity,
            COUNT(*) - COUNT(DISTINCT hadm_id) AS duplicate_admissions
        FROM cohort
    """).fetchdf().iloc[0]
    counts = {name: int(value) for name, value in row.items()}
    counts["patients_in_multiple_splits"] = int(con.execute("""
        SELECT COUNT(*) FROM (
            SELECT subject_id FROM cohort GROUP BY subject_id HAVING COUNT(DISTINCT split) > 1
        )
    """).fetchone()[0])
    con.close()
    digest = hashlib.sha256()
    with cohort.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {
        "run_id": "P01b-input-timing-v1",
        "cohort_sha256": digest.hexdigest(),
        "source_headers": headers,
        "cohort_checks": counts,
        "actual_predictor_fields": ["chiefcomplaint", "acuity", "home_meds"],
        "conclusions": {
            "triage": "No per-row timestamp in this source; admission-time availability of chiefcomplaint and acuity is assumed, not verified.",
            "medrecon": "Charttime is bounded by the builder; absence of storetime prevents verifying entry availability.",
            "labs": "Not used by current predictors. Future inputs must gate both charttime and storetime; audit not yet performed on lab rows.",
            "vitals": "Triage vitals are stored but not used by current predictors. Timestamped vitalsign rows can support a future charttime filter; entry time remains unverified.",
            "targets": "Prescription starttime defines the historical target window; it is not an order-authoring timestamp.",
        },
        "next_required_work": [
            "Define a primary input policy and prespecified sensitivity excluding fields without verified availability.",
            "Audit clinical evidence fields before generating review cards.",
            "Do not claim zero prospective information leakage from zero charttime violations.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--restricted", type=Path, default=ROOT)
    parser.add_argument("--cohort", type=Path, default=ROOT / "prismatic-v3/cohort_atc4_6h.parquet")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "results/input_timing_audit.json")
    args = parser.parse_args()
    report = audit(args.restricted, args.cohort)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"run_id": report["run_id"], "cohort_checks": report["cohort_checks"],
                      "timestamp_columns": {k: v["timestamp_columns"] for k, v in report["source_headers"].items()}}, indent=2))
