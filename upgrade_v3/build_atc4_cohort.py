"""Build a restricted, patient-split ATC-L4 historical-order cohort.

The public SafeDrug NDC map is pinned by SHA in the report. GSN fallback is
learned from training patients only. No patient-level artifact is written to
the repository. This is order imitation, not clinical appropriateness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path.home() / "Desktop/MedTreeBench/dataset/restricted"
V3 = ROOT / "prismatic-v3"
BASE = V3 / "admission_cohort_6h.parquet"
PRESCRIPTIONS = ROOT / "mimiciv/3.1/hosp/prescriptions.csv.gz"
PUBLIC_MAP = Path("/tmp/prismatic-safedrug/data/input/RXCUI2atc4.csv")
SPLIT_SALT = "patient-split-2026"


def split_patient(value: object) -> str:
    digest = hashlib.blake2b(f"{SPLIT_SALT}:{value}".encode(), digest_size=8).digest()
    bucket = int.from_bytes(digest, "big") % 10
    return "test" if bucket == 0 else "val" if bucket == 1 else "train"


def ndc11(value: str) -> str | None:
    if not isinstance(value, str):
        return None
    groups = value.strip().split("-")
    if len(groups) == 1:
        return value if len(value) == 11 and value.isdigit() else None
    if len(groups) != 3 or not all(g.isdigit() for g in groups):
        return None
    lengths = tuple(map(len, groups))
    if lengths == (5, 4, 2):
        return "".join(groups)
    if lengths == (4, 4, 2):
        return "0" + "".join(groups)
    if lengths == (5, 3, 2):
        return groups[0] + "0" + groups[1] + groups[2]
    if lengths == (5, 4, 1):
        return groups[0] + groups[1] + "0" + groups[2]
    return None


def build(base: Path, prescriptions: Path, public_map: Path, output: Path,
          min_gsn_support: int = 10, min_gsn_purity: float = 0.98) -> dict:
    output.parent.mkdir(parents=True, exist_ok=True)
    map_bytes_sha = hashlib.sha256(public_map.read_bytes()).hexdigest()
    raw_map = pd.read_csv(public_map, dtype=str, usecols=["NDC", "ATC4"])
    raw_map["ndc11"] = raw_map.NDC.map(ndc11)
    raw_map = raw_map.dropna(subset=["ndc11", "ATC4"])
    raw_map = raw_map[raw_map.ATC4.str.fullmatch(r"[A-Z][0-9]{2}[A-Z]{2}")]
    # Historical NDC assignments can be ambiguous; never choose an arbitrary code.
    ambiguity = raw_map.groupby("ndc11").ATC4.nunique()
    unique_ndc = set(ambiguity[ambiguity.eq(1)].index)
    mapping = raw_map[raw_map.ndc11.isin(unique_ndc)].drop_duplicates("ndc11")[["ndc11", "ATC4"]]
    cohort = pd.read_parquet(base, columns=["subject_id", "hadm_id"])
    cohort["split"] = cohort.subject_id.map(split_patient)
    assert cohort.groupby("subject_id").split.nunique().max() == 1

    con = duckdb.connect()
    con.execute("PRAGMA threads=4")
    con.register("cohort_splits", cohort)
    con.register("public_ndc_map", mapping)
    con.execute("CREATE TEMP TABLE base AS SELECT * FROM read_parquet(?)", [str(base)])
    con.execute("CREATE TEMP TABLE ndc_map AS SELECT * FROM public_ndc_map")
    con.execute("CREATE TEMP TABLE splits AS SELECT * FROM cohort_splits")
    con.execute("""
        CREATE TEMP TABLE orders AS
        SELECT b.hadm_id, s.split, TRIM(p.gsn) AS gsn,
               LOWER(TRIM(p.drug)) AS drug_name,
               TRIM(p.ndc) AS ndc, m.ATC4 AS direct_atc4
        FROM read_csv(?, all_varchar=true) p
        JOIN base b ON p.hadm_id = b.hadm_id AND p.subject_id = b.subject_id
        JOIN splits s ON b.hadm_id = s.hadm_id
        LEFT JOIN ndc_map m ON TRIM(p.ndc) = m.ndc11
        WHERE TRY_CAST(p.starttime AS TIMESTAMP) >= b.decision_time
          AND TRY_CAST(p.starttime AS TIMESTAMP) < b.decision_time + INTERVAL 6 HOUR
    """, [str(prescriptions)])
    # A GSN is accepted only if train patients provide enough NDC-mapped
    # examples and at least 98% agree on the same ATC-L4 code.
    con.execute("""
        CREATE TEMP TABLE gsn_map AS
        WITH counts AS (
            SELECT gsn, direct_atc4 AS atc4, COUNT(*) AS n
            FROM orders WHERE split = 'train' AND gsn IS NOT NULL
              AND gsn <> '' AND direct_atc4 IS NOT NULL
            GROUP BY 1, 2
        ), ranked AS (
            SELECT *, SUM(n) OVER (PARTITION BY gsn) AS total,
                   ROW_NUMBER() OVER (PARTITION BY gsn ORDER BY n DESC, atc4) AS rank
            FROM counts
        )
        SELECT gsn, atc4 FROM ranked
        WHERE rank = 1 AND total >= ? AND n * 1.0 / total >= ?
    """, [min_gsn_support, min_gsn_purity])
    con.execute("""
        CREATE TEMP TABLE drug_name_map AS
        WITH counts AS (
            SELECT drug_name, direct_atc4 AS atc4, COUNT(*) AS n
            FROM orders WHERE split = 'train' AND drug_name IS NOT NULL
              AND drug_name <> '' AND direct_atc4 IS NOT NULL
            GROUP BY 1, 2
        ), ranked AS (
            SELECT *, SUM(n) OVER (PARTITION BY drug_name) AS total,
                   ROW_NUMBER() OVER (PARTITION BY drug_name ORDER BY n DESC, atc4) AS rank
            FROM counts
        )
        SELECT drug_name, atc4 FROM ranked
        WHERE rank = 1 AND total >= ? AND n * 1.0 / total >= ?
    """, [min_gsn_support, min_gsn_purity])
    con.execute("""
        CREATE TEMP TABLE mapped AS
        SELECT o.*, COALESCE(o.direct_atc4, g.atc4, d.atc4) AS atc4,
               CASE WHEN o.direct_atc4 IS NOT NULL THEN 'ndc'
                    WHEN g.atc4 IS NOT NULL THEN 'train_gsn'
                    WHEN d.atc4 IS NOT NULL THEN 'train_drug_name'
                    ELSE 'unmapped' END AS map_source
        FROM orders o LEFT JOIN gsn_map g USING (gsn)
        LEFT JOIN drug_name_map d USING (drug_name)
    """)
    con.execute("""
        CREATE TEMP TABLE labels AS
        SELECT hadm_id, LIST_SORT(LIST_DISTINCT(LIST(atc4))) AS atc4_codes
        FROM mapped WHERE atc4 IS NOT NULL GROUP BY hadm_id
    """)
    con.execute("""
        COPY (SELECT b.*, s.split, COALESCE(l.atc4_codes, []::VARCHAR[]) AS atc4_codes
              FROM base b JOIN splits s USING (hadm_id)
              LEFT JOIN labels l USING (hadm_id))
        TO ? (FORMAT PARQUET, COMPRESSION ZSTD)
    """, [str(output)])
    order_counts = con.execute("""
        SELECT COUNT(*), COUNT(*) FILTER (WHERE ndc ~ '^[0-9]{11}$'),
               COUNT(*) FILTER (WHERE map_source = 'ndc'),
               COUNT(*) FILTER (WHERE map_source = 'train_gsn'),
               COUNT(*) FILTER (WHERE map_source = 'train_drug_name'),
               COUNT(*) FILTER (WHERE map_source = 'unmapped'),
               COUNT(DISTINCT atc4) FROM mapped
    """).fetchone()
    cohort_counts = con.execute("""
        SELECT split, COUNT(*), COUNT(DISTINCT subject_id),
               COUNT(*) FILTER (WHERE LEN(atc4_codes) > 0),
               SUM(LEN(atc4_codes))
        FROM read_parquet(?) GROUP BY split ORDER BY split
    """, [str(output)]).fetchall()
    report = {
        "task": "historical all-route ATC-L4 order-set prediction within 6h; not clinical correctness",
        "population": "all ED-to-hospital admissions with admission during ED stay; no future-order inclusion rule",
        "source_map": "SafeDrug official RXCUI2atc4.csv commit 88ce5c377dcdc2aa01aaa88f5478dfa4373ba49a",
        "source_map_sha256": map_bytes_sha,
        "ndc_normalization": "only standard 10-digit hyphenated or exact 11-digit forms; ambiguous NDC excluded",
        "public_unambiguous_ndc": len(unique_ndc),
        "gsn_fallback": {"training_patients_only": True, "minimum_mapped_orders": min_gsn_support,
                         "minimum_purity": min_gsn_purity,
                         "accepted_gsn_codes": con.execute("SELECT COUNT(*) FROM gsn_map").fetchone()[0]},
        "drug_name_fallback": {"training_patients_only": True, "minimum_mapped_orders": min_gsn_support,
                               "minimum_purity": min_gsn_purity,
                               "accepted_names": con.execute("SELECT COUNT(*) FROM drug_name_map").fetchone()[0]},
        "split": f"patient-disjoint BLAKE2b({SPLIT_SALT}), 80/10/10",
        "orders": {"all": order_counts[0], "with_11digit_ndc": order_counts[1],
                   "mapped_ndc": order_counts[2], "mapped_train_gsn_fallback": order_counts[3],
                   "mapped_train_drug_name_fallback": order_counts[4],
                   "unmapped": order_counts[5], "unique_atc4": order_counts[6],
                   "mapped_fraction": round(sum(order_counts[2:5]) / order_counts[0], 5)},
        "cohort_by_split": {name: {"admissions": n, "patients": patients,
                                    "with_mapped_label": with_label, "mapped_label_instances": label_n}
                            for name, n, patients, with_label, label_n in cohort_counts},
        "restricted_source_cohort": str(base),
        "restricted_patient_level_output": str(output),
    }
    con.close()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, default=BASE)
    parser.add_argument("--prescriptions", type=Path, default=PRESCRIPTIONS)
    parser.add_argument("--public-map", type=Path, default=PUBLIC_MAP)
    parser.add_argument("--output", type=Path, default=V3 / "cohort_atc4_6h.parquet")
    parser.add_argument("--audit", type=Path, default=Path(__file__).parent / "results/atc4_mapping_audit.json")
    args = parser.parse_args()
    result = build(args.base, args.prescriptions, args.public_map, args.output)
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.audit.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
