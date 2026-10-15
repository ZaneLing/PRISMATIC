"""Offline review components. Coverage is not a clinical safety determination.

No credential access, remote calls, clinical writes, or automatic dose changes.
The measured public-QA checkpoint is pinned in evaluated_profile.json; this new
review layer is not retroactively credited with that checkpoint's scores.
"""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SECTIONS = ('indications_and_usage', 'contraindications', 'drug_interactions',
            'dosage_and_administration', 'use_in_specific_populations',
            'boxed_warning', 'warnings_and_cautions', 'warnings')


def norm(value):
    return ' '.join(re.findall(r'[a-z0-9]+', str(value).lower()))


class LabelIndex:
    """Exact source-alias retrieval in question AND options; no label inference.

    Formulation applicability remains unresolved. Matching a drug mention is
    not confirmation that its label applies to the requested route or product.
    """
    def __init__(self, path):
        path = Path(path)
        self.source_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        self.records = []
        for _, record in sorted(json.loads(path.read_text()).items()):
            if record.get('status') != 'matched' or not record.get('label'):
                continue
            label = record['label']
            names = label.get('openfda') or {}
            aliases = {norm(a) for field in ('generic_name', 'brand_name')
                       for a in names.get(field, []) if len(norm(a)) >= 4}
            if aliases and label.get('id'):
                self.records.append((aliases, label))

    def query(self, question, options=(), max_excerpts=8):
        text = ' ' + norm(str(question) + ' ' + ' '.join(options)) + ' '
        words = set(text.split())
        matched = {}
        for aliases, label in self.records:
            found = sorted(a for a in aliases if ' ' + a + ' ' in text)
            if found:
                matched[label['id']] = (found, label)
        evidence = []
        for label_id, (aliases, label) in sorted(matched.items()):
            for section in SECTIONS:
                values = label.get(section) or []
                if isinstance(values, str):
                    values = [values]
                for paragraph_index, value in enumerate(values):
                    # Contiguous source spans preserve exact provenance.
                    for offset in range(0, min(len(value), 30000), 600):
                        excerpt = value[offset:offset + 800]
                        if len(excerpt.strip()) < 20:
                            continue
                        overlap = len(words & set(norm(excerpt).split()))
                        evidence.append({'label_id': label_id,
                            'set_id': label.get('set_id'),
                            'effective_time': label.get('effective_time'),
                            'matched_aliases': aliases, 'section': section,
                            'paragraph_index': paragraph_index, 'offset': offset, 'quote': excerpt,
                            'overlap': overlap, 'source_sha256': self.source_sha256})
        evidence.sort(key=lambda e: (-e['overlap'], e['label_id'], e['section'], e['offset']))
        return {'status': 'retrieved_unverified_applicability' if evidence else 'not_assessed',
                'label_ids': sorted(matched), 'excerpts': evidence[:max_excerpts],
                'formulation_applicability': 'not_assessed',
                'clinical_safety': 'not_assessed'}


class RxRSIAgent:
    """One orchestration entry point with explicit unassessed clinical domains.

    `actor` receives a context, not gold labels. Existing QA inference can be
    connected as a callable; tests use deterministic actors. `assess` reports
    structural conflicts and tool requirements, never a blanket safe verdict.
    """
    def __init__(self, actor=None, label_index=None):
        self.actor = actor
        self.labels = label_index
        self.registry = json.loads((HERE / 'clinical_skills.json').read_text())
        self.profile = json.loads((HERE / 'evaluated_profile.json').read_text())
        skill_path = HERE.parent / self.profile['skill_path']
        skill_bytes = skill_path.read_bytes()
        if hashlib.sha256(skill_bytes).hexdigest() != self.profile['skill_sha256']:
            raise ValueError('Selected skill does not match the frozen profile')
        self.skill = skill_bytes.decode('utf-8')

    def prepare(self, question, options=(), patient=None):
        evidence = self.labels.query(question, options) if self.labels else {
            'status': 'not_assessed', 'excerpts': [], 'clinical_safety': 'not_assessed'}
        return {'question': question, 'options': list(options), 'patient': patient or {},
                'evidence': evidence, 'policy': self.registry['invariants'],
                'skill_memory': {'text': self.skill, 'sha256': self.profile['skill_sha256'],
                    'authority': 'experience_not_clinical_guidance'}}

    def run(self, question, options=(), patient=None):
        context = self.prepare(question, options, patient)
        if self.actor is None:
            return {'status': 'needs_actor', 'context': context}
        output = self.actor(context)
        if not isinstance(output, dict):
            return {'status': 'invalid_output', 'output': None}
        if options:
            answer = output.get('final')
            valid = answer in [chr(65+i) for i in range(len(options))]
            return {'status': 'completed' if valid else 'invalid_output',
                    'output': output, 'evidence': context['evidence']}
        return {'status': 'reviewed_draft', 'output': output,
                'review': self.assess(patient or {}, output.get('orders', []))}

    def assess(self, patient, orders):
        issues = []
        if not isinstance(orders, list):
            return {'status': 'invalid_order_container', 'clinical_safety': 'not_assessed'}
        if not orders:
            issues.append({'code': 'empty_order_set_requires_justification'})
        required = ('ingredient_id', 'indication', 'dose', 'dose_unit', 'route', 'frequency', 'duration')
        seen = set()
        allergies = patient.get('allergy_ingredient_ids')
        if allergies is None:
            issues.append({'code': 'allergy_status_missing'})
        elif not isinstance(allergies, list) or any(not isinstance(a, str) for a in allergies):
            issues.append({'code': 'invalid_allergy_list'})
            allergies = None
        for index, order in enumerate(orders):
            if not isinstance(order, dict):
                issues.append({'code': 'invalid_order', 'order': index})
                continue
            for field in required:
                if order.get(field) in (None, ''):
                    issues.append({'code': 'missing_' + field, 'order': index})
            ingredient = order.get('ingredient_id')
            if ingredient is not None and not isinstance(ingredient, str):
                issues.append({'code': 'invalid_ingredient_id', 'order': index})
                ingredient = None
            if ingredient and ingredient in seen:
                issues.append({'code': 'potential_duplicate_ingredient', 'order': index})
            if ingredient:
                seen.add(ingredient)
            if ingredient and allergies and ingredient in allergies:
                issues.append({'code': 'recorded_ingredient_allergy', 'order': index})
            dose = order.get('dose')
            if isinstance(dose, bool) or not isinstance(dose, (int, float)) or not (0 < dose < float('inf')):
                issues.append({'code': 'dose_not_positive_finite_number', 'order': index})
            if order.get('role') == 'adjunct' and not order.get('linked_indication'):
                issues.append({'code': 'adjunct_purpose_missing', 'order': index})
            if norm(order.get('route', '')) in ('iv', 'intravenous'):
                if order.get('administration_mode') not in ('push', 'infusion'):
                    issues.append({'code': 'iv_mode_missing', 'order': index})
                for field in ('preparation_evidence', 'administration_rate_evidence'):
                    if not order.get(field):
                        issues.append({'code': 'missing_' + field, 'order': index})
        return {'status': 'requires_resolution' if issues else 'structurally_complete',
                'issues': issues, 'clinical_safety': 'not_assessed',
                'clinical_domains': [{'id': s['id'], 'status': 'not_assessed',
                    'required_tools': s['tools'], 'required_facts': s['required_facts']}
                    for s in self.registry['skills']]}

    @staticmethod
    def admit_memory(record):
        """Validate an experience proposal; promotion is a separate experiment."""
        required = ('scope', 'source_hashes', 'trigger', 'action', 'counterexamples')
        if record.get('split') != 'train':
            return {'accepted': False, 'reason': 'training_experience_only'}
        if any(not record.get(k) for k in required):
            return {'accepted': False, 'reason': 'incomplete_provenance_or_scope'}
        if record.get('authority') != 'experience_not_clinical_guidance':
            return {'accepted': False, 'reason': 'invalid_authority'}
        return {'accepted': True, 'status': 'candidate_requires_development_validation'}
