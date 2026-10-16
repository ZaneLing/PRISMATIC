"""Preserve complete source sentences around retrieved windows.

This is a researcher-authored tool repair, not autonomous code evolution.
The retrieved candidate set and language-model calls are unchanged from v45.
"""
import collections
import json
import re
import threading
from common45 import RUN as SOURCE_RUN
from evidence45 import Evidence45


def sentence_bounds(text, start, end):
    # Preserve original bytes and offsets. Decimal points are not boundaries.
    cuts = [0] + [m.end() for m in re.finditer(r'(?<=[.!?])\s+(?=[A-Z(])|\n+', text)] + [len(text)]
    left = max(x for x in cuts if x <= start)
    right = min(x for x in cuts if x >= end)
    return left, right


class Evidence46(Evidence45):
    def __init__(self):
        super().__init__()
        self.full = {}
        self.seen_files = set()
        self.lock = threading.Lock()

    def query(self, case, plan, policy=None):
        original = super().query(case, plan, policy)
        with self.lock:
            for path in (SOURCE_RUN / 'full_labels').glob('*.json'):
                if path in self.seen_files:
                    continue
                record = json.loads(path.read_text())
                if record['status'] != 'reserved':
                    self.seen_files.add(path)
                    self.full.update({x['id']: x for x in record.get('labels', [])})
        budget = original['char_budget']
        expanded, flags = [], list(original['flags'])
        for span in original['excerpts']:
            label = self.full[span['label_id']]
            values = label[span['section']]
            values = [values] if isinstance(values, str) else values
            full_text = values[span['paragraph']]
            start, end = sentence_bounds(full_text, span['offset'], span['offset'] + len(span['quote']))
            expanded.append(dict(span, offset=start, quote=full_text[start:end],
                                 previous_offset=span['offset'], previous_length=len(span['quote'])))
        # First ensure each option can receive one full span. Later spans may be
        # dropped for budget; never silently remove a sentence's qualifications.
        first, rest, seen = [], [], set()
        for span in expanded:
            if span['option'] not in seen:
                first.append(span); seen.add(span['option'])
            else:
                rest.append(span)
        selected = []
        for span in first + rest:
            if len(span['quote']) > budget:
                flags.append({'status': 'whole_sentence_omitted_for_budget', 'label_id': span['label_id'], 'option': span['option']})
                continue
            span['evidence_id'] = 'E' + str(len(selected) + 1)
            selected.append(span); budget -= len(span['quote'])
        return dict(original, excerpts=selected, flags=flags, chars_used=original['char_budget'] - budget,
                    scope=original['scope'] + ' Whole sentence boundaries preserved; full clinical qualifier entailment remains unverified.')
