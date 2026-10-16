"""Training-only route attribution audit; no patient-level public output."""
from collections import Counter
from common import *
from route_evidence import route_status

def main():
    data = load_cases(); counts = Counter(); cases = Counter()
    for rnd in range(1, 7):
        rows = json.loads((PRIVATE/f'train-before-{rnd}.json').read_text())['rows']
        for c, row in zip(data['train'][(rnd-1)*24:rnd*24], rows):
            assert c['case_id'] == row['case_id']
            statuses = []
            for span in row['evidence']['spans']:
                status = route_status(c['catalogue'][span['order_id']]['route'], span['source_route'])
                counts[status] += 1; statuses.append(status)
            for status in set(statuses): cases[status] += 1
    save(HERE/'results/route_evidence_audit.json', {
        'training_cases': 144, 'excerpts': sum(counts.values()),
        'excerpt_status_counts': dict(counts), 'case_status_counts': dict(cases),
        'interpretation': 'Declared source-route overlap only; no-overlap is not a contraindication. PO/NG overlap with ORAL alone is partial, not verified tube suitability.',
        'source': 'https://www.fda.gov/drugs/data-standards-manual-monographs/route-administration'})
    print(dict(counts))

if __name__ == '__main__': main()
