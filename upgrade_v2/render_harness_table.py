"""Render the public paired experiment as publication-ready Markdown tables."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


NAMES = {
    "openai/gpt-6.1-sol": "GPT-6.1 Sol",
    "google/gemini-3.8-flash": "Gemini 3.8 Flash",
    "deepseek/deepseek-v4.1-flash": "DeepSeek V4.1 Flash",
}


def pct(value: float) -> str:
    return f"{100 * value:+.1f}"


def interval(comparison: dict) -> str:
    lo, hi = comparison["ci95"]
    return f"{pct(comparison['delta'])} [{pct(lo)}, {pct(hi)}]"


def render(report: dict, language: str) -> str:
    if report["n"] != 60:
        raise ValueError("Expected the fixed 60-question public sample")
    if language == "zh":
        header = "| 模型 | 直接作答 | 普通二次复核 | 证据约束 harness | Δ harness−直接（百分点，95% CI） | Δ harness−普通复核（百分点，95% CI） | 改对 / 改错 |\n| --- | ---: | ---: | ---: | ---: | ---: | ---: |"
        secondary = "| 模型 | 禁忌：直接 → harness | 相互作用：直接 → harness | harness 合约通过 /60 | harness 最终有效 /60 | 两次调用费用：普通 / harness（美元） |\n| --- | ---: | ---: | ---: | ---: | ---: |"
    elif language == "en":
        header = "| Model | Direct | Ordinary second review | Evidence-constrained harness | Δ harness−direct (pp, 95% CI) | Δ harness−review (pp, 95% CI) | Corrected / harmed |\n| --- | ---: | ---: | ---: | ---: | ---: | ---: |"
        secondary = "| Model | Contraindication: direct → harness | Interaction: direct → harness | Harness contract accepted /60 | Valid final answer /60 | Two-call cost: review / harness (USD) |\n| --- | ---: | ---: | ---: | ---: | ---: |"
    else:
        raise ValueError(language)
    main = [header]
    details = [secondary]
    for model in NAMES:
        scores = report["model_results"][model]
        arms = scores["arms"]
        def cell(arm: str) -> str:
            data = arms[arm]
            return f"{data['correct']}/60 ({100 * data['accuracy']:.1f}%)"
        h = arms["harness"]
        main.append(
            f"| {NAMES[model]} | {cell('direct')} | {cell('repeat')} | {cell('harness')} | "
            f"{interval(scores['harness_minus_direct'])} | "
            f"{interval(scores['harness_minus_repeat'])} | "
            f"{h['corrected']} / {h['harmed']} |"
        )
        by = lambda kind, arm: f"{arms[arm]['by_type'][kind]['correct']}/30"
        contract = h["status_counts"].get("kept", 0) + h["status_counts"].get("changed", 0)
        details.append(
            f"| {NAMES[model]} | {by('contraindication', 'direct')} → "
            f"{by('contraindication', 'harness')} | "
            f"{by('interaction', 'direct')} → {by('interaction', 'harness')} | "
            f"{contract}/60 | {h['valid_letter']}/60 | "
            f"${arms['repeat']['two_call_cost_usd']:.4f} / ${h['two_call_cost_usd']:.4f} |"
        )
    return "\n".join(main) + "\n\n" + "\n".join(details)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, default=Path(__file__).parent /
                        "results/openrouter_rxsafe_harness_pilot.json")
    parser.add_argument("--language", choices=("zh", "en"), required=True)
    args = parser.parse_args()
    print(render(json.loads(args.result.read_text()), args.language))
