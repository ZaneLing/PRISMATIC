"""Guard budget and label isolation for the new real-state task adapter."""
import sys,types,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'upgrade_v14'))
from fhir_executor import run_case

class ExecutionContracts(unittest.TestCase):
    case={'id':'task1_contract','instruction':'Return an empty result for this synthetic protocol test.','context':'No patient involved.','sol':[],'eval_MRN':'not-visible'}
    grader=types.SimpleNamespace(task1=lambda case,result,base: result.result=='[]')

    def test_repairs_use_the_original_eight_call_budget(self):
        r=run_case(self.case,'verified_state_harness',self.grader,actor=lambda h:{'raw':'extra prose'},repair_protocol=True,compile_payloads=True)
        self.assertEqual(r['model_calls'],8);self.assertEqual(r['status'],'round_limit');self.assertFalse(r['live_execution_correct'])
        replies=iter(['extra prose','FINISH([])'])
        r=run_case(self.case,'verified_state_harness',self.grader,actor=lambda h:{'raw':next(replies)},repair_protocol=True,compile_payloads=True)
        self.assertEqual(r['model_calls'],2);self.assertTrue(r['live_execution_correct'])

    def test_eval_fields_do_not_change_actor_inputs(self):
        prompts=[]
        def actor(h):prompts.append(h.copy());return {'raw':'FINISH([])'}
        run_case(self.case,'verified_state_harness',self.grader,actor=actor)
        changed=dict(self.case,sol=['changed secret label'],eval_MRN='changed-hidden-identity')
        run_case(changed,'verified_state_harness',self.grader,actor=actor)
        self.assertEqual(prompts[0],prompts[1])

if __name__=='__main__':unittest.main()
