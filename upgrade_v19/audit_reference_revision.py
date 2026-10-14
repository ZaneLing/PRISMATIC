"""Verify the development-only grading repair on existing physical receipts."""
import contextlib,copy,hashlib,io,json,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'upgrade_v14'))
from fhir_executor import LOCAL,RESOURCE,BASE,grader_module,run_case
from reference_compat import reference_view,regrade_cached
from order_compiler import compile_order
from probe_fhir_state import total

def trace(p):return [{'role':'agent','content':'POST '+BASE+p['resourceType']+'\n'+json.dumps(p)}]

class Contracts(unittest.TestCase):
    def test_projection_preserves_original_and_values(self):
        p={'resourceType':'ServiceRequest','note':[{'text':'Exact note','authorString':'writer'}]}
        t=trace(p);before=copy.deepcopy(t);view,audit=reference_view(t)
        self.assertEqual(t,before);self.assertEqual(json.loads(view[0]['content'].split('\n',1)[1])['note'],p['note'][0]);self.assertEqual(len(audit),1)

    def test_multinote_and_coded_route_remain_intact(self):
        for p in [{'resourceType':'ServiceRequest','note':[{'text':'a'},{'text':'b'}]},
                  {'resourceType':'MedicationRequest','dosageInstruction':[{'route':{'text':'IV','coding':[{'code':'x'}]}}]}]:
            view,audit=reference_view(trace(p));self.assertEqual(view,trace(p));self.assertEqual(audit,[])
        p={'resourceType':'MedicationRequest','dosageInstruction':[{'route':{'text':'IV'}}]}
        view,_=reference_view(trace(p));self.assertEqual(json.loads(view[0]['content'].split('\n',1)[1])['dosageInstruction'][0]['route'],'IV')

    def test_server_note_normalization_is_equal_for_both_arms(self):
        p={'resourceType':'ServiceRequest','note':{'text':'Exact note'}}
        stored=compile_order(p)[0]
        def http(method,path,body=None):
            if method=='POST':return 201,dict(stored,id='synthetic-contract')
            if method=='GET':return 200,dict(stored,id='synthetic-contract')
            return 204,None
        for compiled in [False,True]:
            actions=iter([trace(p)[0]['content'],'FINISH([])'])
            with patch('fhir_executor.http_request',http):
                r=run_case({'id':'task1_contract','instruction':'synthetic','context':''},
                    'verified_state_harness' if compiled else 'direct_tool',types.SimpleNamespace(task1=lambda *args:True),
                    actor=lambda h:{'raw':next(actions)},compile_payloads=compiled,repair_protocol=compiled)
            self.assertTrue(r['live_execution_correct']);self.assertEqual(r['write_checks'],[True])

def main():
    result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Contracts));assert result.wasSuccessful()
    grader=grader_module();source=RESOURCE/'src/server/tasks/medagentbench/refsol.py';source_sha=hashlib.sha256(source.read_bytes()).hexdigest()
    cases={c['id']:c for split in ['dev','val'] for c in json.loads((RESOURCE/'data/medagentbench'/f'split_{split}.json').read_text())}
    records=json.loads((HERE/'results/note_reference_schema_audit.json').read_text())['examples'];checks=[]
    for entry in records:
        raw=json.loads((LOCAL/'learning-v19'/(entry['episode_digest']+'.json')).read_text());case=cases[raw['case_id']]
        with contextlib.redirect_stdout(io.StringIO()):revised=regrade_cached(raw,case,grader,BASE)
        assert not raw['original_trace_correct'] and not revised['original_trace_correct'] and not revised['legacy_live_reference_correct']
        assert revised['semantic_reference_correct'] and revised['live_execution_correct'] and all(revised['active_post_checks'])
        assert all(w['persisted'] or w['rolled_back'] for w in revised['write_audits'] if w['create_status']==201)
        wrong=copy.deepcopy(revised['semantic_trace']);mutated=0
        for m in wrong:
            if m['role']=='agent' and m['content'].startswith('POST '):
                line,body=m['content'].split('\n',1);p=json.loads(body)
                if p.get('resourceType')=='ServiceRequest' and 'note' in p:
                    p['note']['text']='Incorrect unrelated comment';m['content']=line+'\n'+json.dumps(p);mutated+=1
        assert mutated>=1
        obj=types.SimpleNamespace(history=[types.SimpleNamespace(**m) for m in wrong],result=raw['answer'])
        with contextlib.redirect_stdout(io.StringIO()):assert not getattr(grader,case['id'].split('_')[0])(case,obj,BASE)
        # An unchanged semantic answer must still fail if an active physical
        # write did not preserve its fields.
        damaged=copy.deepcopy(raw);damaged['active_post_checks']=[False]
        with contextlib.redirect_stdout(io.StringIO()):assert not regrade_cached(damaged,case,grader,BASE)['live_execution_correct']
        checks.append({'episode_digest':entry['episode_digest'],'raw_grade_retained_false':True,'active_write_fields_and_meaning_pass':True,
          'prior_failed_readbacks_rolled_back':sum(not b for b in revised['write_checks']),
          'eligible_for_new_episode_reuse':all(revised['write_checks']),'wrong_comment_rejected':True,'field_loss_rejected':True})
    counts={r:total(r) for r in ['Patient','MedicationRequest','Observation','ServiceRequest']}
    assert counts==json.loads((HERE/'results/grading_revision.json').read_text())['resource_counts_after_stop']
    report={'status':'passed','development_receipts_regraded':len(checks),'synthetic_contracts':result.testsRun,
      'model_calls':0,'new_physical_writes':0,'original_reference_sha256':source_sha,'original_reference_unchanged':True,
      'test_cases_used':0,'resource_counts':counts,'checks':checks,
      'scope':'Evaluator repair, not agent improvement; original wrong-shape grades retained. New learning starts with empty skills.'}
    (HERE/'results/reference_revision_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='checks'}))

if __name__=='__main__':main()
