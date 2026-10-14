"""Create a restricted case manifest for a future two-reviewer blinded study.

This does not expose cases, predictions, or original orders in the repository.
The review packet must be assembled only after every method can emit complete
orders with route, dose, volume and rate, and pre-decision evidence is audited.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
from build_atc4_cohort import split_patient

ROOT = Path.home() / "Desktop/MedTreeBench/dataset/restricted"


def run(source: Path, output: Path, per_stratum: int = 25) -> dict:
    frame = pd.read_parquet(source, columns=["subject_id", "hadm_id", "saline_iv",
                                                 "ondansetron", "bowel_regimen"])
    frame = frame.loc[frame.subject_id.map(split_patient).eq("test")].copy()
    frame["stratum"] = (frame.saline_iv.astype(str) + frame.ondansetron.astype(str)
                        + frame.bowel_regimen.astype(str))
    frame["rank"] = frame.hadm_id.map(lambda value: hashlib.sha256(
        f"review-sample-v1:{value}".encode()).hexdigest())
    sample = (frame.sort_values("rank").groupby("stratum", group_keys=False)
              .head(per_stratum).copy())
    sample["case_code"] = sample.hadm_id.map(lambda value: hashlib.sha256(
        f"review-case-v1:{value}".encode()).hexdigest()[:12])
    assert sample.case_code.is_unique
    output.parent.mkdir(parents=True, exist_ok=True)
    # IDs and historical-label strata are restricted; reviewers receive only
    # coded, blinded clinical cards once source evidence is compiled.
    sample[["case_code", "subject_id", "hadm_id", "stratum"]].to_csv(output, index=False)
    result = {
        "sample_size": len(sample),
        "eligible_test_strata_counts": {str(k): int(v) for k, v in frame.stratum.value_counts().sort_index().items()},
        "strata_counts": {str(k): int(v) for k, v in sample.stratum.value_counts().sort_index().items()},
        "strata_bits": ["historical_IV_0.9pct_saline", "historical_ondansetron",
                        "historical_senna_or_docusate"],
        "status": "case manifest only; no clinician judgments, candidate orders or review cards yet",
        "patient_split": "common test patients only; patient-split-2026",
        "restricted_manifest": str(output),
    }
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=ROOT / "prismatic-v3/supportive_cohort_6h.parquet")
    ap.add_argument("--output", type=Path, default=ROOT / "prismatic-v3/review_manifest.csv")
    ap.add_argument("--audit", type=Path, default=Path(__file__).parent / "results/review_sample_audit.json")
    a = ap.parse_args()
    report = run(a.source, a.output)
    a.audit.parent.mkdir(parents=True, exist_ok=True)
    a.audit.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
