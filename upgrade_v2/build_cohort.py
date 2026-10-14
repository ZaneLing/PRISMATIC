"""Build a local, time-bounded MIMIC-IV ED-to-hospital medication cohort.

Patient-level output is restricted and stays under the restricted data root. Only aggregate audit
statistics are printed. The task is historical order-set prediction, not a
clinical safety benchmark or a prescription recommendation system.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
from paths import ARTIFACT_DIR, RESTRICTED_ROOT


DEFAULT_RESTRICTED = RESTRICTED_ROOT
LOCAL_DIR = ARTIFACT_DIR


def source(root: Path, relative: str) -> str:
    path = root / relative
    if not path.is_file():
        raise FileNotFoundError(path)
    return str(path).replace("'", "''")


def build(root: Path, hours: int, output: Path, include_unlabeled: bool = False) -> dict:
    if not 1 <= hours <= 24:
        raise ValueError("hours must be between 1 and 24")
    output.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("PRAGMA threads=4")

    ed = source(root, "mimic-iv-ed-v2.2/ed/edstays.csv.gz")
    admissions = source(root, "mimiciv/3.1/hosp/admissions.csv.gz")
    triage = source(root, "mimic-iv-ed-v2.2/ed/triage.csv.gz")
    medrecon = source(root, "mimic-iv-ed-v2.2/ed/medrecon.csv.gz")
    prescriptions = source(root, "mimiciv/3.1/hosp/prescriptions.csv.gz")

    # Select one ED stay for each admission. The admission must occur during
    # that ED stay; diagnosis and discharge tables are deliberately unused.
    con.execute(f"""
        CREATE TEMP TABLE base AS
        SELECT e.subject_id, e.stay_id, e.hadm_id,
               TRY_CAST(e.intime AS TIMESTAMP) AS ed_intime,
               TRY_CAST(e.outtime AS TIMESTAMP) AS ed_outtime,
               TRY_CAST(a.admittime AS TIMESTAMP) AS decision_time,
               a.race
        FROM read_csv('{ed}', all_varchar=true) e
        JOIN read_csv('{admissions}', all_varchar=true) a
          ON e.hadm_id = a.hadm_id AND e.subject_id = a.subject_id
        WHERE e.hadm_id IS NOT NULL
          AND TRY_CAST(e.intime AS TIMESTAMP) <= TRY_CAST(a.admittime AS TIMESTAMP)
          AND TRY_CAST(a.admittime AS TIMESTAMP) <= TRY_CAST(e.outtime AS TIMESTAMP)
        QUALIFY ROW_NUMBER() OVER
          (PARTITION BY e.hadm_id ORDER BY TRY_CAST(e.intime AS TIMESTAMP) DESC, e.stay_id) = 1
    """)
    con.execute(f"""
        CREATE TEMP TABLE triage_input AS
        SELECT t.stay_id, t.chiefcomplaint, t.acuity,
               t.heartrate, t.resprate, t.o2sat, t.sbp, t.dbp,
               t.temperature
        FROM read_csv('{triage}', all_varchar=true) t
        JOIN base b ON t.stay_id = b.stay_id
    """)
    con.execute(f"""
        CREATE TEMP TABLE home_med_input AS
        SELECT b.stay_id,
               ARRAY_TO_STRING(LIST_SLICE(LIST_SORT(LIST_DISTINCT(
                   LIST(LOWER(TRIM(m.name))))), 1, 30), ' | ') AS home_meds,
               COUNT(DISTINCT LOWER(TRIM(m.name))) AS home_med_count,
               MAX(TRY_CAST(m.charttime AS TIMESTAMP)) AS max_home_med_charttime
        FROM read_csv('{medrecon}', all_varchar=true) m
        JOIN base b ON m.stay_id = b.stay_id AND m.subject_id = b.subject_id
        WHERE TRY_CAST(m.charttime AS TIMESTAMP) BETWEEN b.ed_intime AND b.decision_time
          AND m.name IS NOT NULL AND TRIM(m.name) <> ''
        GROUP BY b.stay_id
    """)
    con.execute(f"""
        CREATE TEMP TABLE labels AS
        SELECT b.hadm_id,
               LIST_SORT(LIST_DISTINCT(LIST(TRIM(p.gsn)))) AS target_codes,
               COUNT(DISTINCT TRIM(p.gsn)) AS target_count,
               MIN(TRY_CAST(p.starttime AS TIMESTAMP)) AS min_target_starttime,
               MAX(TRY_CAST(p.starttime AS TIMESTAMP)) AS max_target_starttime
        FROM read_csv('{prescriptions}', all_varchar=true) p
        JOIN base b ON p.hadm_id = b.hadm_id AND p.subject_id = b.subject_id
        WHERE TRY_CAST(p.starttime AS TIMESTAMP) >= b.decision_time
          AND TRY_CAST(p.starttime AS TIMESTAMP) < b.decision_time + INTERVAL {hours} HOUR
          AND p.route IN ('PO', 'PO/NG', 'ORAL', 'NG', 'SL')
          AND p.gsn IS NOT NULL AND TRIM(p.gsn) <> ''
        GROUP BY b.hadm_id
    """)

    escaped_output = str(output).replace("'", "''")
    label_join = "LEFT JOIN" if include_unlabeled else "JOIN"
    con.execute(f"""
        COPY (
            SELECT b.subject_id, b.hadm_id, b.stay_id, b.decision_time,
                   b.race, t.chiefcomplaint, t.acuity, t.heartrate,
                   t.resprate, t.o2sat, t.sbp, t.dbp, t.temperature,
                   COALESCE(h.home_meds, '') AS home_meds,
                   COALESCE(h.home_med_count, 0) AS home_med_count,
                   h.max_home_med_charttime,
                   COALESCE(l.target_codes, []::VARCHAR[]) AS target_codes,
                   COALESCE(l.target_count, 0) AS target_count,
                   l.min_target_starttime, l.max_target_starttime
            FROM base b
            LEFT JOIN triage_input t ON b.stay_id = t.stay_id
            LEFT JOIN home_med_input h ON b.stay_id = h.stay_id
            {label_join} labels l ON b.hadm_id = l.hadm_id
        ) TO '{escaped_output}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    audit = con.execute(f"""
        SELECT COUNT(*) AS admissions, COUNT(DISTINCT subject_id) AS patients,
               COUNT(*) FILTER (WHERE chiefcomplaint IS NOT NULL AND TRIM(chiefcomplaint) <> '') AS with_chief_complaint,
               COUNT(*) FILTER (WHERE home_med_count > 0) AS with_pre_admission_medrecon,
               APPROX_QUANTILE(target_count, [0.1, 0.5, 0.9, 0.99]) AS target_count_quantiles,
               AVG(target_count) AS mean_target_count,
               COUNT(*) FILTER (WHERE max_home_med_charttime > decision_time
                    OR min_target_starttime < decision_time
                    OR max_target_starttime >= decision_time + INTERVAL {hours} HOUR) AS temporal_violations,
               COUNT(*) - COUNT(DISTINCT hadm_id) AS duplicate_admissions
        FROM read_parquet('{escaped_output}')
    """).fetchone()
    base_count = con.execute("SELECT COUNT(*) FROM base").fetchone()[0]
    medrecon_timing = con.execute(f"""
        SELECT COUNT(*) FILTER (WHERE TRY_CAST(m.charttime AS TIMESTAMP)
                                    BETWEEN b.ed_intime AND b.decision_time),
               COUNT(*) FILTER (WHERE TRY_CAST(m.charttime AS TIMESTAMP) > b.decision_time)
        FROM read_csv('{medrecon}', all_varchar=true) m
        JOIN base b ON m.stay_id = b.stay_id AND m.subject_id = b.subject_id
    """).fetchone()
    result = {
        "task": "historical_oral_gsn_set_within_hours_after_hospital_admission",
        "selection": ("all ED-to-hospital admissions at decision time; zero-order labels retained"
                      if include_unlabeled else "requires a future oral-GSN order"),
        "hours": hours,
        "base_admissions_with_ed_stay_covering_admission": base_count,
        "cohort_admissions": audit[0],
        "cohort_patients": audit[1],
        "with_chief_complaint": audit[2],
        "with_pre_admission_medrecon": audit[3],
        "pre_admission_medrecon_rows_in_source": medrecon_timing[0],
        "post_admission_medrecon_rows_excluded": medrecon_timing[1],
        "target_count_quantiles_p10_p50_p90_p99": audit[4],
        "mean_target_count": round(audit[5], 3),
        "temporal_violations": audit[6],
        "duplicate_admissions": audit[7],
        "input_sources": ["ED stay", "ED triage", "medrecon charted by decision_time", "hospital admissions"],
        "label_source": "hospital prescriptions, starttime in [decision_time, decision_time + hours)",
        "excluded_as_inputs": ["discharge notes", "discharge diagnosis", "later labs", "later medications"],
        "clinical_interpretation": "historical behavior prediction only; no safety or appropriateness labels",
    }
    audit_path = output.parent / f"cohort_audit_{hours}h.json"
    audit_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    if result["temporal_violations"] or result["duplicate_admissions"]:
        raise AssertionError("cohort failed temporal or uniqueness audit")
    con.close()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--restricted", type=Path, default=DEFAULT_RESTRICTED)
    parser.add_argument("--hours", type=int, default=6)
    parser.add_argument("--output", type=Path, default=LOCAL_DIR / "cohort_6h.parquet")
    parser.add_argument("--include-unlabeled", action="store_true",
                        help="Keep all ED-to-hospital admissions; do not select on future oral orders")
    args = parser.parse_args()
    print(json.dumps(build(args.restricted, args.hours, args.output,
                           include_unlabeled=args.include_unlabeled), indent=2, ensure_ascii=False))
