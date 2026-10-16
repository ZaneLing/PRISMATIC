"""Product-scope retrieval: full label metadata, option roles, and combinations.

No benchmark answers, drug-frequency model, or drug-to-answer rules are read.
An ingredient's name alone does not establish product equivalence.
"""
import collections
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from common45 import RUN, digest, save
from evidence import LabelTool, FIELDS, norm, routes
from evidence37 import DEFAULT, forms
from sklearn.feature_extraction.text import TfidfVectorizer

LOCK = threading.RLock()
NEXT = [0.0]
FETCH_LOCKS = {}
MAX_REQUESTS = 800
EXTRA_FIELDS = ('purpose', 'active_ingredient', 'dosage_forms_and_strengths', 'spl_unclassified_section')


def homeopathic(label):
    """Explicit label classification, never brand/manufacturer-name guessing."""
    text = json.dumps(label, ensure_ascii=False).lower()
    return bool(re.search(r'\bhomeopath(?:ic|y)\b|\bhomoeopathic\b|\bHPUS\b', text, re.I))


def identity_matches(components, label):
    checker = LabelTool.__new__(LabelTool)
    if len(components) == 1:
        return checker.identity_ok(components[0], label)
    of = label.get('openfda') or {}
    substances = of.get('substance_name', [])
    # Every requested component must have a distinct matched source substance;
    # extra active components are not silently treated as equivalent.
    if len(substances) != len(components):
        return False
    matches = [{j for j, substance in enumerate(substances)
                if set(norm(component).split()) <= set(norm(substance).split())}
               for component in components]
    import itertools
    return any(all(j in matches[i] for i, j in enumerate(order))
               for order in itertools.permutations(range(len(substances))))


def fetch_full(components, route=''):
    key = digest([components, route])
    folder = RUN / 'full_labels'
    folder.mkdir(exist_ok=True)
    path = folder / (key + '.json')
    with LOCK:
        lock = FETCH_LOCKS.setdefault(key, threading.Lock())
    with lock:
        if path.exists():
            return json.loads(path.read_text())
        # Reserve slots while holding the global lock, including concurrent calls.
        with LOCK:
            if len(list(folder.glob('*.json'))) >= MAX_REQUESTS:
                return {'status': 'query_limit', 'labels': []}
            save(path, {'status': 'reserved', 'labels': []})
            delay = max(0, NEXT[0] - time.monotonic())
            NEXT[0] = max(NEXT[0], time.monotonic()) + .35
        if delay:
            time.sleep(delay)
        clauses = ['(openfda.generic_name:"' + name + '" OR openfda.brand_name:"' + name + '" OR openfda.substance_name:"' + name + '")' for name in components]
        query = ' AND '.join(clauses)
        if route:
            query += ' AND openfda.route:"' + route.upper() + '"'
        url = 'https://api.fda.gov/drug/label.json?' + urllib.parse.urlencode({'search': query, 'limit': 100, 'sort': 'effective_time:desc'})
        result = {'url': url, 'components': components, 'route': route, 'labels': []}
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'RxRSIAgent-product-scope-study'}), timeout=30) as response:
                raw = response.read()
            payload = json.loads(raw)
            result.update(status='retrieved', response_sha256=__import__('hashlib').sha256(raw).hexdigest(),
                          labels=[x for x in payload.get('results', []) if x.get('effective_time', '') <= '20261016'])
        except urllib.error.HTTPError as error:
            result['status'] = 'http_' + str(error.code)
        except (OSError, ValueError) as error:
            result['status'] = type(error).__name__
        save(path, result)
        return result


def entity_groups(case, plan, known_aliases):
    text = case['dialogue'] + '\n' + '\n'.join(case['options'])
    groups = {}
    for i, option in enumerate(case['options']):
        if norm(option) in known_aliases:
            groups[(norm(option), chr(65 + i))] = {'name': norm(option), 'option': chr(65 + i), 'route': ''}
    for entity in plan.get('entities', []):
        if not isinstance(entity, dict):
            continue
        name, quote, option = norm(entity.get('name', '')), entity.get('input_quote'), str(entity.get('option', 'context'))
        if not name or len(name) > 90 or not isinstance(quote, str) or not quote or quote not in text:
            continue
        if not set(name.split()) <= set(norm(quote).split()):
            continue
        if option != 'context' and option not in [chr(65 + i) for i in range(len(case['options']))]:
            continue
        # A medication repeated in two alternatives keeps BOTH option roles.
        groups[(name, option)] = {'name': name, 'option': option, 'route': entity.get('route', '')}
    output = [dict(x, components=[x['name']], scope='component') for x in groups.values()]
    by_option = collections.defaultdict(list)
    for entity in groups.values():
        if entity['option'] != 'context':
            by_option[entity['option']].append(entity)
    for option, entities in by_option.items():
        wording = case['options'][ord(option) - 65]
        # Distinguish a joint regimen from an option saying to replace X with Y.
        joint = bool(re.search(r'[-+/]|\band\b|\bplus\b', wording, re.I))
        if 2 <= len(entities) <= 3 and joint and not re.search(r'\b(?:instead|switch|replace|versus|rather)\b', wording, re.I):
            components = sorted({x['name'] for x in entities})
            if len(components) >= 2:
                output.append({'name': ' + '.join(components), 'components': components, 'option': option,
                               'route': '', 'scope': 'combination'})
    return output


class Evidence45(LabelTool):
    def query(self, case, plan, policy=None):
        policy = policy or DEFAULT
        entities = entity_groups(case, plan, self.by_alias)
        products, flags, spans = [], [], collections.defaultdict(list)
        focus = plan.get('focus', '')
        focus = focus if isinstance(focus, str) else ' '.join(x for x in focus if isinstance(x, str)) if isinstance(focus, list) else ''
        query = focus + ' ' + case['dialogue']
        for entity in entities:
            record = fetch_full(entity['components'], entity['route'])
            candidates = []
            for label in record['labels']:
                if not identity_matches(entity['components'], label):
                    continue
                if homeopathic(label):
                    flags.append({'status': 'homeopathic_scope_not_conventional_evidence', 'label_id': label['id'], 'option': entity['option']})
                    continue
                label_routes = routes(' '.join((label.get('openfda') or {}).get('route', [])))
                if entity['route'] and label_routes and entity['route'] not in label_routes:
                    continue
                indication = ' '.join(label.get('indications_and_usage') or [])
                score = len(set(norm(focus).split()) & set(norm(indication).split()))
                candidates.append((-score, label['id'], label, label_routes))
            candidates.sort(key=lambda x: x[:2])
            picked, signatures = [], set()
            for _, _, label, label_routes in candidates:
                signature = (tuple(label_routes), tuple(forms(label)))
                if signature in signatures:
                    continue
                signatures.add(signature)
                picked.append((label, label_routes))
                if len(picked) == policy['variants']:
                    break
            if not picked:
                flags.append({'status': 'no_scope_verified_label', 'name': entity['name'], 'option': entity['option'], 'source_status': record['status']})
            for label, label_routes in picked:
                of = label.get('openfda') or {}
                products.append(dict(entity, label_id=label['id'], set_id=label.get('set_id'), routes=label_routes,
                                     generic=of.get('generic_name', []), unii=of.get('unii', []),
                                     release_forms=forms(label), product_type=of.get('product_type', []),
                                     route_status='matched' if entity['route'] and label_routes else 'unknown',
                                     approval_status='not_inferred_from_presence_in_openFDA'))
                chunks = []
                for field in FIELDS + EXTRA_FIELDS:
                    values = label.get(field) or []
                    values = [values] if isinstance(values, str) else values
                    for paragraph, value in enumerate(values):
                        for offset in range(0, len(value), max(400, policy['window'] // 2)):
                            quote = value[offset:offset + policy['window']]
                            if len(quote.strip()) >= 30:
                                chunks.append(dict(label_id=label['id'], set_id=label.get('set_id'), date=label.get('effective_time'), section=field, paragraph=paragraph, offset=offset, quote=quote, name=entity['name'], option=entity['option'], product_scope=entity['scope']))
                if not chunks:
                    continue
                vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), sublinear_tf=True, max_features=20000)
                matrix = vectorizer.fit_transform([x['quote'] for x in chunks])
                scores = (matrix @ vectorizer.transform([query]).T).toarray()[:, 0]
                for fields in [('indications_and_usage', 'purpose'), ('dosage_and_administration', 'dosage_forms_and_strengths'), ('contraindications', 'drug_interactions', 'use_in_specific_populations', 'boxed_warning', 'warnings_and_cautions', 'warnings')]:
                    indices = [i for i, x in enumerate(chunks) if x['section'] in fields]
                    if indices:
                        spans[entity['option']].append(chunks[max(indices, key=lambda i: (scores[i], -i))])
        # Equal option opportunities; combination-level evidence precedes components.
        for option in spans:
            spans[option].sort(key=lambda x: (x['product_scope'] != 'combination', x['section'] not in ('indications_and_usage', 'purpose')))
        excerpt_list = []
        budget = policy['char_budget']
        span_length = min(policy['window'], max(250, budget // max(1, sum(len(v) for v in spans.values()))))
        for slot in range(max([len(v) for v in spans.values()] or [0])):
            for option in sorted(spans, key=lambda x: (x == 'context', x)):
                if slot < len(spans[option]) and budget >= 100:
                    span = dict(spans[option][slot]); span['quote'] = span['quote'][:min(span_length, budget)]
                    span['evidence_id'] = 'E' + str(len(excerpt_list) + 1)
                    budget -= len(span['quote']); excerpt_list.append(span)
        return {'products': products, 'excerpts': excerpt_list, 'flags': flags,
                'chars_used': policy['char_budget'] - budget, 'char_budget': policy['char_budget'],
                'scope': 'Product/regimen evidence only. Missing evidence is unknown; a source quotation does not establish clinical applicability or FDA approval.'}
