"""Guard budget and label isolation for the new real-state task adapter."""
import sys,types,unittest,tempfile
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

    def test_all_released_task_schemas_allow_missing_literal_solutions(self):
        from fhir_task import FHIRTask
        task=FHIRTask()
        for split,count in [('dev',96),('val',80),('id_test',64),('test',60)]:
            samples=task.samples(split)
            self.assertEqual(len(samples),count)
            for c in samples:
                if 'sol' not in c:self.assertIsNone(c['answer'])
                self.assertTrue(callable(getattr(task.grader,c['type'])))

    def test_grader_failure_cannot_become_a_model_error(self):
        def broken(case,result,base):raise RuntimeError('synthetic evaluator outage')
        with self.assertRaisesRegex(RuntimeError,'Reference grading failed'):
            run_case(self.case,'verified_state_harness',types.SimpleNamespace(task1=broken),actor=lambda h:{'raw':'FINISH([])'})

    def test_task_wrapper_and_exact_episode_replay(self):
        from fhir_task import FHIRTask
        from grasp.skills.agent import SkillAwareAgent
        from grasp.skills.repository import SkillRepository
        class ScriptedBackend:
            def __init__(self):self.latest=types.SimpleNamespace();self.calls=0
            def inference(self,history,tools=None):
                self.calls+=1;self.latest.response={'raw':'FINISH([])'};return 'FINISH([])'
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);skills=root/'skills';skills.mkdir()
            task=FHIRTask();task.cache=root/'cache';task.cache.mkdir()
            backend=ScriptedBackend();agent=SkillAwareAgent(backend,SkillRepository(base_dir=skills,learned_dir=skills))
            first=task.rollout(self.case,agent);second=task.rollout(self.case,agent)
            self.assertEqual(backend.calls,1)
            self.assertTrue(task.evaluate(self.case,first));self.assertTrue(task.evaluate(self.case,second))
            self.assertEqual(first.raw['episode_digest'],second.raw['episode_digest'])

if __name__=='__main__':unittest.main()
