"""Grounded skill evolution using the unchanged, credited GRASP optimizer."""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'upgrade_v10'))
sys.path.insert(0,str(HERE.parent/'upgrade_v11'))
from grasp_task import MedicationTask,PublicBackend
from evidence_tool import LabelEvidence

class GroundedMedicationTask(MedicationTask):
    name='grounded-rxsafebench-option-selection'
    updater_guidance=MedicationTask.updater_guidance+' Drug-label excerpts are supplied by a frozen retrieval tool. Learn how to apply or reject their relevance to documented patient facts; missing excerpts never establish safety. Do not copy individual questions or gold letters into skills.'

    def __init__(self):
        super().__init__();self.evidence=LabelEvidence();self.views={}
        for cases in list(self.parts.values())+[self.transfer]:
            for c in cases:
                self.views[c['id']]=self.evidence.query(c,'balanced')

    def rollout(self,sample,agent):
        view=dict(sample)
        view['dialogue']=sample['dialogue']+'\nDrug-label tool excerpts (company-submitted labels via openFDA; incomplete excerpts, apply only to documented patient facts; missing text is not proof of safety):\n'+json.dumps(self.views[sample['id']],ensure_ascii=False)
        return super().rollout(view,agent)
