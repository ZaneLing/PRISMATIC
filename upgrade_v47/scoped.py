"""Apply a product repair only in its source-verified/structural scope."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
for folder in ['upgrade_v45', 'upgrade_v46']:
    sys.path.insert(0, str(ROOT / folder))
from common45 import digest
from runtime import RuntimeAgent, RobustEvidence
from evidence45 import entity_groups
from evidence46 import Evidence46


def reasons(case, plan, old_evidence):
    registry = json.loads((ROOT / 'upgrade_v47/source_registry.json').read_text())
    home = set(registry['explicitly_homeopathic_label_ids'])
    result = []
    if any(x['label_id'] in home for x in old_evidence['products']):
        result.append('source_classified_homeopathic_product')
    if any(x['scope'] == 'combination' for x in entity_groups(case, plan, {})):
        result.append('joint_regimen_in_option')
    return result


class ScopeEvidence(RobustEvidence):
    def __init__(self):
        super().__init__()
        self.repaired = Evidence46()

    def query(self, case, plan, policy=None):
        original = super().query(case, plan, policy)
        return self.repaired.query(case, plan, policy) if reasons(case, plan, original) else original


class ScopedAgent(RuntimeAgent):
    def __init__(self, state=None):
        super().__init__(state)
        self.labels = ScopeEvidence()
