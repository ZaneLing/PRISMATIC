"""Attach descriptive supportive-order labels to the leakage-audited admission cohort.

This is a pilot conditioned on an oral order in the first six hours because it
reuses cohort_6h.parquet. These labels describe historical orders; they do not
establish that an order was clinically indicated or safe.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb

from paths import ARTIFACT_DIR, RESTRICTED_ROOT


LABELS = ("saline_iv", "ondansetron", "bowel_regimen")


def build(base: Path, prescriptions: Path, output: Path) -> dict:
    output.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("PRAGMA threads=4")
    con.execute("CREATE TEMP TABLE cohort AS SELECT * FROM read_parquet(?)", [str(base)])
    con.execute("""
        CREATE TEMP TABLE label_rows AS
        SELECT c.hadm_id,
               TRY_CAST(p.starttime AS TIMESTAMP) AS starttime,
               CASE
                 WHEN lower(trim(p.drug)) IN
                      ('0.9% sodium chloride', 'sodium chloride 0.9%',
                       '0.9 % sodium chloride', 'isotonic sodium chloride')
                      AND p.route IN ('IV', 'IV DRIP') THEN 'saline_iv'
                 WHEN lower(trim(p.drug)) IN ('ondansetron', 'ondansetron odt')
                      THEN 'ondansetron'
                 WHEN lower(trim(p.drug)) IN
                      ('senna', 'docusate sodium', 'docusate sodium (liquid)')
                      THEN 'bowel_regimen'
               END AS label
        FROM read_csv(?, all_varchar=true) p
        JOIN cohort c ON p.hadm_id = c.hadm_id AND p.subject_id = c.subject_id
        WHERE TRY_CAST(p.starttime AS TIMESTAMP) >= c.decision_time
          AND TRY_CAST(p.starttime AS TIMESTAMP) < c.decision_time + INTERVAL 6 HOUR
    """, [str(prescriptions)])
    con.execute("""
        CREATE TEMP TABLE label_sets AS
        SELECT hadm_id,
               CAST(COUNT(*) FILTER (WHERE label = 'saline_iv') > 0 AS INT) AS saline_iv,
               CAST(COUNT(*) FILTER (WHERE label = 'ondansetron') > 0 AS INT) AS ondansetron,
               CAST(COUNT(*) FILTER (WHERE label = 'bowel_regimen') > 0 AS INT) AS bowel_regimen
        FROM label_rows GROUP BY hadm_id
    """)
    con.execute("""
        COPY (SELECT c.*, COALESCE(l.saline_iv, 0) AS saline_iv,
                    COALESCE(l.ondansetron, 0) AS ondansetron,
                    COALESCE(l.bowel_regimen, 0) AS bowel_regimen
              FROM cohort c LEFT JOIN label_sets l USING (hadm_id))
        TO ? (FORMAT PARQUET, COMPRESSION ZSTD)
    """, [str(output)])
    counts = con.execute("""
        SELECT COUNT(*), COUNT(DISTINCT subject_id),
               SUM(saline_iv), SUM(ondansetron), SUM(bowel_regimen),
               COUNT(*) FILTER (WHERE min_target_starttime < decision_time
                   OR max_target_starttime >= decision_time + INTERVAL 6 HOUR)
        FROM read_parquet(?)
    """, [str(output)]).fetchone()
    report = {
        "task": "historical supportive-order occurrence in first six hours after admission",
        "population": "ED-to-hospital admissions with at least one oral-GSN order in six hours",
        "admissions": counts[0], "patients": counts[1],
        "positive_admissions": dict(zip(LABELS, counts[2:5])),
        "prevalence": {name: round(counts[i] / counts[0], 5)
                       for i, name in enumerate(LABELS, start=2)},
        "base_temporal_violations": counts[5],
        "label_definition": {
            "saline_iv": "exactly named 0.9% sodium chloride/isotonic saline, IV or IV DRIP; excludes flushes and carrier bags by name",
            "ondansetron": "ondansetron or ondansetron ODT, any route",
            "bowel_regimen": "senna or docusate sodium, any route",
        },
        "interpretation": "historical order imitation only; no appropriateness or safety labels",
    }
    (output.parent / "supportive_cohort_audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    con.close()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, default=ARTIFACT_DIR / "cohort_6h.parquet")
    parser.add_argument("--prescriptions", type=Path, default=RESTRICTED_ROOT / "mimiciv/3.1/hosp/prescriptions.csv.gz")
    parser.add_argument("--output", type=Path, default=ARTIFACT_DIR / "supportive_cohort_6h.parquet")
    args = parser.parse_args()
    print(json.dumps(build(args.base, args.prescriptions, args.output), ensure_ascii=False, indent=2))
