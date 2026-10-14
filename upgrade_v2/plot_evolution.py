"""Create a shareable aggregate learning-curve figure (no patient records)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


def plot(source: Path, output: Path) -> None:
    report = json.loads(source.read_text())
    rows = report["curves"]
    sizes = [row["cases_seen"] for row in rows]
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    fig.subplots_adjust(left=0.14, right=0.98, top=0.88, bottom=0.22)
    for key, label, color, marker in [
        ("prevalence_baseline", "Prevalence baseline", "#777777", "o"),
        ("case_memory_knn30", "Case memory (30 neighbors)", "#2574a9", "s"),
        ("incremental_sgd", "Incremental logistic SGD", "#c75826", "^"),
    ]:
        values = [row[key]["macro_average_precision"] for row in rows]
        ax.plot(sizes, values, marker=marker, linewidth=2, markersize=6,
                label=label, color=color)
    ax.set_xscale("log")
    ax.set_xticks(sizes, [f"{n:,}" for n in sizes])
    ax.set_ylim(0.29, 0.54)
    ax.set_xlabel("Cumulative training admissions")
    ax.set_ylabel("Macro average precision across 3 order labels")
    ax.set_title("Learning historical supportive-order patterns")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend(frameon=False, loc="upper left")
    fig.text(0.02, 0.045, "Fixed patient-disjoint test (n=1,000). Historical order matching; not clinical appropriateness.",
             fontsize=8, color="#555555")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path,
                        default=Path(__file__).parent / "results/evolution_curve.json")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).parent / "results/evolution_curve.png")
    args = parser.parse_args()
    plot(args.source, args.output)
