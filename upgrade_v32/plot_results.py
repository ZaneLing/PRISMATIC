"""Plot every audited repair/control at fixed and calibrated endpoints."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
LABELS = {
    'frozen_base': 'Frozen base',
    'original_failed_adapter': 'Original failed adapter',
    'teacher_uniform': 'GT prefix / uniform loss',
    'zero_uniform': 'Zero prefix / uniform loss',
    'teacher_balanced': 'GT prefix / balanced loss',
    'zero_balanced': 'Zero prefix / balanced loss',
    'original_retrieval_top8': 'Original retrieval top-8',
    'all20_candidate_tools': 'All 20 candidate tools',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(split):
    summary_path = HERE / f'results/{split}_summary.json'
    audit_path = HERE / f'results/{split}_audit.json'
    data = json.loads(summary_path.read_text())
    audit = json.loads(audit_path.read_text())
    assert audit['status'] == 'passed' and audit['summary_sha256'] == sha(summary_path)
    assert audit['auditor_sha256'] == sha(HERE / 'audit_evaluation.py')
    conditions = data['views']
    endpoints = ['fixed_half', 'proposal_calibrated']
    names = list(LABELS)
    assert all(set(data['endpoints'][e][v]['methods']) == set(names)
               for e in endpoints for v in conditions)
    plt.rcParams['svg.hashsalt'] = 'rxrsi-v32-repair-results'
    fig, axes = plt.subplots(2, len(conditions), figsize=(6 * len(conditions), 8.5),
                             sharex='row', sharey=True, squeeze=False)
    y = np.arange(len(names))
    maximum = max(data['endpoints'][e][v]['methods'][m]['drug_micro_f1']
                  for e in endpoints for v in conditions for m in names)
    for column, view in enumerate(conditions):
        for row, (metric, scale, label) in enumerate([
                ('drug_micro_f1', 1, 'Drug micro-F1'), ('empty_fraction', 100, 'Empty outputs (%)')]):
            ax = axes[row, column]
            values = [np.array([data['endpoints'][e][view]['methods'][m][metric]
                                for m in names]) * scale for e in endpoints]
            assert all(np.isfinite(v).all() for v in values)
            for k in range(len(names)):
                ax.plot([values[0][k], values[1][k]], [y[k] - .1, y[k] + .1],
                        color='#A5ACB5', lw=1, zorder=1)
            ax.scatter(values[0], y - .1, marker='o', color='#277C8E', s=28,
                       label='Fixed threshold 0.5', zorder=2)
            ax.scatter(values[1], y + .1, marker='s', color='#D88921', s=24,
                       label='Proposal-calibrated threshold', zorder=2)
            ax.set_yticks(y)
            ax.set_yticklabels(list(LABELS.values()), fontsize=9)
            ax.tick_params(axis='y', labelleft=column == 0, length=0)
            ax.set_xlabel(label, fontsize=10)
            ax.grid(axis='x', alpha=.2)
            ax.set_axisbelow(True)
            ax.set_xlim((-2, 102) if row else (-.01, min(1.02, max(.2, maximum * 1.15))))
            ax.axhline(1.5, lw=.7, color='#C3C8CC')
            ax.axhline(5.5, lw=.7, color='#C3C8CC')
            for edge in ['top', 'right', 'left']:
                ax.spines[edge].set_visible(False)
            if row == 0:
                ax.set_title(view.capitalize() + ' candidates', fontsize=11)
    axes[0, 0].set_ylim(len(names) - .5, -.5)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', ncol=2, frameon=False,
               bbox_to_anchor=(.57, .055), fontsize=9)
    fig.suptitle(f'Controlled decision repair: {data["cases"]} {split} admissions, one training seed', fontsize=13)
    note = ('Proposal data select the thresholds; this figure is development evidence.' if split == 'proposal'
            else 'Reused development guard; every state and threshold was frozen before evaluation.')
    fig.text(.57, .025, note, ha='center', fontsize=9)
    fig.subplots_adjust(left=.25, right=.97, top=.91, bottom=.16, hspace=.36, wspace=.13)
    png = HERE / f'{split}_repair.png'
    svg = HERE / f'{split}_repair.svg'
    fig.savefig(png, dpi=180)
    fig.savefig(svg, metadata={'Date': None})
    plt.close(fig)
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n')
    receipt = {'status': 'rendered_from_audited_scores', 'split': split,
               'summary_sha256': sha(summary_path), 'audit_sha256': sha(audit_path),
               'script_sha256': sha(Path(__file__)), 'png_sha256': sha(png), 'svg_sha256': sha(svg),
               'methods': names, 'endpoints': endpoints, 'views': conditions,
               'intervals_shown': False, 'new_model_inference': False}
    (HERE / f'results/{split}_figure.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': receipt['status'], 'split': split, 'methods': len(names)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('split', choices=['proposal', 'guard'])
    main(parser.parse_args().split)
