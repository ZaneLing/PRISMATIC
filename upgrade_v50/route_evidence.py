"""Filter unsupported label-route attribution, never prohibit an order.

FDA SPL distinguishes NASAL from NASOGASTRIC. PO/NG is disjunctive;
an ORAL label alone does not establish suitability for a feeding tube.
Absent overlap is not proof of a clinical contraindication or invalid off-label use.
"""
import heapq
import evidence

ALIASES = {
    'po': {'ORAL'}, 'oral': {'ORAL'},
    'iv': {'INTRAVENOUS', 'INTRAVENOUS BOLUS', 'INTRAVENOUS DRIP'},
    'po/ng': {'ORAL', 'NASOGASTRIC'},
}

def route_status(order_route, source_routes):
    target = ALIASES.get(str(order_route).strip().lower())
    source = {str(x).strip().upper() for x in source_routes or []}
    if not target or not source:
        return 'unknown'
    if not target & source:
        return 'no_declared_overlap'
    if str(order_route).lower() == 'po/ng' and not {'ORAL', 'NASOGASTRIC'} <= source:
        return 'partial_disjunctive_overlap'
    return 'declared_overlap_not_clinical_approval'

def retrieve(c, plan):
    source = evidence.bank()
    words = set(evidence.normalize(c['input'] + ' ' + plan).split())
    found = {}; matched = 0
    for cid, order in c['catalogue'].items():
        labels = source.get(evidence.normalize(order['drug_name']), {})
        matched += bool(labels)
        for lid, label in labels.items():
            routes = label.get('openfda', {}).get('route', [])
            if route_status(order.get('route'), routes) == 'no_declared_overlap':
                continue
            for section in ['indications_and_usage', 'dosage_and_administration', 'contraindications']:
                for sentence in evidence.sentences(' '.join(label.get(section) or [])):
                    overlap = len(words & evidence.sentence_words(sentence))
                    item = (-overlap, cid, lid, section, sentence, routes)
                    if sentence not in found or item[:5] < found[sentence][:5]:
                        found[sentence] = item
    top = heapq.nsmallest(2, found.values(), key=lambda x: x[:5])
    spans = [{'order_id':cid, 'source_id':lid, 'section':section,
              'source_route':routes, 'quote':sentence}
             for _, cid, lid, section, sentence, routes in top]
    # Keep the original interface/wording to isolate source eligibility.
    return {'matched_candidate_drugs': matched,
            'candidate_drugs': len(c['catalogue']), 'spans': spans,
            'limits': 'Exact cached product identity only. Retrieved text does not establish patient indication or correct dose; route compatibility is not inferred. No fresh network queries.'}
