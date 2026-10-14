"""Exercise the full common-test evaluator on isolated synthetic files only."""
import contextlib,copy,hashlib,io,json,os,subprocess,sys,tempfile
from pathlib import Path
import joblib,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path[:0]=[str(ROOT),str(HERE)]
from upgrade_v30 import evaluate_program_tests as run
from upgrade_v30 import audit_program_tests as audit
from upgrade_v27.evaluation_metrics import score
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(z):return hashlib.sha256(json.dumps(z,sort_keys=True).encode()).hexdigest()
def write(p,z):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(z)+'\n')
def main():
    gate=subprocess.run([sys.executable,str(HERE/'evaluate_program_tests.py')],cwd=ROOT,capture_output=True,text=True)
    assert gate.returncode!=0 and 'Common extension remains closed:' in gate.stderr and 'ModuleNotFoundError' not in gate.stderr
    with tempfile.TemporaryDirectory(prefix='rxrsi-synthetic-common-test-') as temp:
        root=Path(temp);private=root/'private';out=private/'prismatic-v30/common-test';out.parent.mkdir(parents=True)
        sources=['upgrade_v30/evaluate_program_tests.py','upgrade_v30/common_test_gate.py','upgrade_v29/programs.py','upgrade_v27/evaluation_metrics.py','upgrade_v27/control_features.py','upgrade_v27/method_runtime.py','upgrade_v30/common_test_addendum.json','upgrade_v29/protocol.json']
        for source in sources:
            destination=root/source;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes((ROOT/source).read_bytes())
        vocab={'diagnoses':['d0','d1'],'procedures':['p0'],'medications':['A','B']}
        patients=[{'subject_hash':'synthetic-one','visits':[{'case_id':'c1','diagnoses':['d0'],'procedures':['p0'],'medications':['A']},{'case_id':'c2','diagnoses':['d1'],'procedures':['p0'],'medications':['B']}]},
                  {'subject_hash':'synthetic-two','visits':[{'case_id':'c3','diagnoses':['unknown'],'procedures':['p0'],'medications':['OOV']},{'case_id':'c4','diagnoses':['d0'],'procedures':['p0'],'medications':[]}]}]
        source=private/'prismatic-v27/visits.joblib';source.parent.mkdir(parents=True);joblib.dump({'data':{'test':patients},'vocab':vocab},source)
        write(root/'upgrade_v27/results/cohort_manifest.json',{'bundle_sha256':sha(source)})
        original={'status':'synthetic_fixture','panels':{}}
        arms29=json.loads((ROOT/'upgrade_v29/protocol.json').read_text())['arms'];arms30=['raw_policy','calibrated_policy']+[f'{m}_C{c}P{p}' for m in ('greedy','own','shuffled') for c in (0,1) for p in (0,1)]
        for panel,meds in [('full',['A','B']),('molecular',['A'])]:
            encoded=[]
            for person in patients:
                visits=[]
                for v in person['visits']:
                    gold=v['medications'] if panel=='full' else [m for m in v['medications'] if m in meds]
                    visits.append({'case_id':v['case_id'],'gold':gold,'codes':[[vocab['diagnoses'].index(d) if d in vocab['diagnoses'] else 2 for d in v['diagnoses']],[0],[meds.index(m) for m in v['medications'] if m in meds]]})
                encoded.append({'subject_hash':person['subject_hash'],'visits':visits})
            b={'data':{'test':encoded},'medications':meds,'sizes':[3,2,len(meds)],'ddi':np.zeros((len(meds),len(meds))),'ddi_covered_indices':list(range(len(meds)))}
            bundle=private/f'prismatic-v27/{panel}-models.joblib';joblib.dump(b,bundle)
            cases=[v for p in encoded for v in p['visits']];people=[p['subject_hash'] for p in encoded for v in p['visits']];gold=[set(v['gold']) for v in cases]
            identity={'case_ids':[v['case_id'] for v in cases],'people':people,'gold':[sorted(g) for g in gold],'medications':meds};write(private/f'prismatic-v27/evaluation/{panel}-case-identity.json',identity)
            prediction=np.zeros((4,len(meds)),dtype=bool);metrics,values,keys=score(prediction,gold,people,meds,b['ddi'],b['ddi_covered_indices'])
            path=private/f'prismatic-v27/evaluation/{panel}-static.npz';np.savez(path,prediction=prediction,patient_scores=values,patient_keys=np.array(keys))
            original['panels'][panel]={'case_identity_sha256':digest(identity),'results':{'static':{'kind':'conventional','prediction_sha256':sha(path),'metrics':metrics}},'methods':{'static':{'runs':1,'metrics':{k:{'mean':v,'seed_sd':None} for k,v in metrics.items() if isinstance(v,(int,float))}}}}
            for seed in (42,137,2026):
                states={v:{'lock':{'bundle_sha256':sha(bundle)},'rounds':[],'selections':{arm:{'round':3} for arm in arms}} for v,arms in [(29,arms29),(30,arms30)]}
                for r in range(1,6):
                    src=private/f'prismatic-v29/{panel}-seed{seed}/round{r}';src.mkdir(parents=True);joblib.dump([.45+.1*i for i in range(len(meds))],src/'base.joblib');np.save(src/'thresholds.npy',np.full(len(meds),.5))
                    fits={'base_file':'base.joblib','model_sha256':{'base.joblib':sha(src/'base.joblib')},'selection':{'threshold':.6}};write(src/'fits.json',fits)
                    for version,arms in [(29,arms29),(30,arms30)]:
                        memories={}
                        for arm in arms:
                            rule={'drug_index':0,'conditions':[{'feature_index':0,'present':True}],'action':'include'}
                            memories[arm]=[{**rule,'id':digest(rule)[:20]}] if arm not in ('raw_policy','calibrated_policy') and r in (2,3) else []
                        row={'arms':{arm:{'memory_sha256':digest(memories[arm]),'best_round':min(r,3)} for arm in arms}}
                        if version==29:row.update(model_sha256=fits['model_sha256'],thresholds_sha256=sha(src/'thresholds.npy'))
                        folder=private/f'prismatic-v{version}/{panel}-seed{seed}/round{r}';write(folder/'memories.json',memories);write(folder/'complete.json',row);states[version]['rounds'].append(row)
                for v,z in states.items():write(root/f'upgrade_v{v}/results/{panel}-seed{seed}.json',z)
        write(root/'upgrade_v27/results/test_summary.json',original)
        synthetic_gate={'status':'open','pending':[],'synthetic_fixture':True}
        run.ROOT=root;run.HERE=root/'upgrade_v30';run.PRIVATE=private;run.OUTPUT=out;run.check=lambda:copy.deepcopy(synthetic_gate)
        audit.ROOT=root;audit.HERE=root/'upgrade_v30';audit.PRIVATE=private;audit.OUTPUT=out;audit.check=lambda:copy.deepcopy(synthetic_gate)
        with contextlib.redirect_stdout(io.StringIO()):run.main();audit.main()
        output=root/'upgrade_v30/results/common_test_summary.json';before=sha(output)
        with contextlib.redirect_stdout(io.StringIO()):run.main()
        assert sha(output)==before,'Completed result changed on resume.'
        result=json.loads((root/'upgrade_v30/results/common_test_audit.json').read_text());assert result['status']=='passed'
        assert all(p['reexecuted_prediction_sets']==315 and p['binary_prediction_disagreements']==0 for p in result['panels'].values())
        z=json.loads(output.read_text());selected=z['panels']['full']['endpoints']['selected']['methods']['v29-own_error_program_agent']['patient_f1']['mean'];final=z['panels']['full']['endpoints']['final']['methods']['v29-own_error_program_agent']['patient_f1']['mean'];assert selected!=final
    proof={'status':'passed','synthetic_only':True,'real_test_predictions_read':False,'real_entry_gate_refused_incomplete_prerequisites':True,'prediction_sets_executed_and_independently_reexecuted':630,'source_sha256':{p:sha(HERE/p) for p in ['evaluate_program_tests.py','audit_program_tests.py','common_test_gate.py','probe_common_test.py']},'checks':['Both full and molecular spaces, with OOV and zero-target behavior','All seven/fourteen arms, three seeds and five raw rounds','Selected states differ from raw-final states','Raw and accepted trajectories and fix/regress counts','Every paired program and conventional-method contrast','Completed-result resume is byte-identical','Production gate remains closed on real experiment']}
    (HERE/'results/common_test_probe.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':main()
