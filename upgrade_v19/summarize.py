"""Regrade every completed task and independently verify actual write receipts."""
import contextlib,hashlib,io,json,sys,types
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path[:0]=[str(ROOT/'upgrade_v14')]
from fhir_executor import grader_module,BASE,LOCAL
from reference_compat import reference_view
from order_compiler import compile_order
from probe_fhir_state import total
RESOURCE=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources/GRASP'

def read(p):return json.loads(p.read_text())

def interval(d):
    rng=np.random.default_rng(42);draws=[]
    for _ in range(4000):draws.append(d[rng.integers(0,len(d),len(d))].mean())
    return {'difference':float(d.mean()),'ci95':np.quantile(draws,[.025,.975]).tolist(),'fixes':int((d>0).sum()),'regressions':int((d<0).sum())}

def patient_interval(d,cases):
    """Preserve within-patient dependence without publishing patient identifiers."""
    patients=[c['eval_MRN'] for c in cases];assert all(patients)
    _,ix=np.unique(patients,return_inverse=True);n=int(ix.max()+1)
    sums=np.bincount(ix,weights=d,minlength=n);sizes=np.bincount(ix,minlength=n)
    rng=np.random.default_rng(42);draws=[]
    for _ in range(4000):
        selected=rng.integers(0,n,n);draws.append(sums[selected].sum()/sizes[selected].sum())
    return {'difference':float(d.mean()),'ci95':np.quantile(draws,[.025,.975]).tolist(),'patients':n,
            'note':'Paired patient-cluster bootstrap within this split; overlapping training patients still prevent new-patient generalization claims.'}

def main():
    report=read(HERE/'results/method_results.json');assert report['status']=='complete'
    counts_now={r:total(r) for r in report['resource_counts_after']}
    assert counts_now==report['resource_counts_before']==report['resource_counts_after']
    assert not list((LOCAL/'active').glob('*.json'))
    grader=grader_module();folder=LOCAL/'grasp-v19';frozen=read(HERE/'results/frozen_skills.json')
    assert not frozen['test_used']
    best=folder/'skills/best'
    assert {str(p.relative_to(best)):hashlib.sha256(p.read_bytes()).hexdigest() for p in best.rglob('*') if p.is_file()}==frozen['skills_sha256']
    correctness={};audits=[];by_type={};summary={'status':'complete','methods':report['methods']}
    for method in ['direct_tools','fixed_compiled','evolving_compiled']:
        correctness[method]={};by_type[method]={}
        for split in ['id_test','test']:
            cases=read(RESOURCE/'benchmarks/MedAgentBench/data/medagentbench'/f'split_{split}.json')
            rows=read(folder/f'{method}-{split}.json');assert [r['case_id'] for r in rows]==[c['id'] for c in cases]
            values=[];types_out={};attempts=losses=rollbacks=active_writes=cleanup=0
            for row,case in zip(rows,cases):
                raw=read(LOCAL/'learning-v19-rev2'/(row['episode_digest']+'.json'))
                assert raw['case_id']==row['case_id'] and raw['model_calls']<=8
                assert not raw['grader_errors']
                for key in ['status','model_calls','tool_calls','cost_usd','writes','write_checks','original_trace_correct','live_execution_correct']:
                    assert raw[key]==row[key]
                assert raw['model_calls']==len(raw['usage']);assert raw['tool_calls']==len(raw['tools'])
                assert abs(sum(u['cost_usd'] or 0 for u in raw['usage'])-raw['cost_usd'])<1e-12
                rechecks=[];active=[]
                for w in raw['write_audits']:
                    attempts+=1
                    if w['create_status']!=201 or not isinstance(w['create_receipt'],dict) or not w['create_receipt'].get('id'):continue
                    p=w['canonical_payload'];stored=w['readback']
                    assert compile_order(w.get('submitted_payload',p))[0]==p
                    valid=w['readback_status']==200 and stored.get('resourceType')==p.get('resourceType') and all(stored.get(k)==v for k,v in p.items() if k not in ['id','meta'])
                    assert valid==w['persisted'];rechecks.append(valid);losses+=int(not valid)
                    if w['rolled_back']:assert w['rollback_status'] in (200,204);rollbacks+=1
                    else:active.append(valid)
                assert rechecks==raw['write_checks'] and active==raw['active_post_checks']
                assert len(active)==raw['writes']==len(raw['cleanup_checks']);active_writes+=len(active);cleanup+=len(raw['cleanup_checks'])
                assert all(c['status'] in (200,204) for c in raw['cleanup_checks'])
                def grade(kind):
                    if raw['status']!='completed' or raw['answer'] is None:return False
                    obj=types.SimpleNamespace(history=[types.SimpleNamespace(**m) for m in raw[kind+'_trace']],result=raw['answer'])
                    with contextlib.redirect_stdout(io.StringIO()):return bool(getattr(grader,case['id'].split('_')[0])(case,obj,BASE))
                projected,conversions=reference_view(raw['live_trace'])
                assert projected==raw['semantic_trace'] and conversions==raw['reference_projection_audits']
                original=grade('original');legacy=grade('live');semantic=grade('semantic');live=semantic and all(active)
                assert legacy==raw['legacy_live_reference_correct'] and semantic==raw['semantic_reference_correct']
                assert original==raw['original_trace_correct'] and live==raw['live_execution_correct']
                values.append(int(live));kind=case['id'].split('_')[0];types_out.setdefault(kind,[]).append(int(live))
            expected=report['methods'][method][split];assert sum(values)==expected['state_correct'] and len(values)==expected['n']
            correctness[method][split]=np.array(values);by_type[method][split]={k:{'n':len(v),'state_correct':sum(v)} for k,v in types_out.items()}
            audits.append({'method':method,'split':split,'case_alignment_reference_regrade_receipt_recount':'passed','write_attempts':attempts,'field_loss_attempts':losses,'rollbacks':rollbacks,'remaining_writes_then_cleaned':active_writes,'cleanup_calls':cleanup})
    pairs={};patient_pairs={}
    for split in ['id_test','test']:
        pairs[split]={};patient_pairs[split]={}
        cases=read(RESOURCE/'benchmarks/MedAgentBench/data/medagentbench'/f'split_{split}.json')
        for a,b in [('fixed_compiled','direct_tools'),('evolving_compiled','fixed_compiled'),('evolving_compiled','direct_tools')]:
            delta=correctness[a][split]-correctness[b][split];key=a+'__minus__'+b
            pairs[split][key]=interval(delta);patient_pairs[split][key]=patient_interval(delta,cases)
    updates=read(folder/'epoch_0/skill_updates.json')
    summary.update(audits=audits,paired=pairs,paired_patient_clusters=patient_pairs,by_task_type=by_type,resource_counts_before=report['resource_counts_before'],resource_counts_after=counts_now,
        updates=[{'round':u['update_cycle']+1,'new_cases':u['batch_size'],'applied':[{'action':a['action'],'name':a['name']} for a in u['applied']]} for u in updates],
        interval_note='Descriptive paired task and patient-cluster bootstrap4000 draws. Patient clustering added before the full study produced results. Task types and patient records overlap across splits. One seed. No multiplicity correction.',
        endpoint='Unchanged original reference evaluated through declared lossless shape views AND preservation of all remaining canonical fields on actual readback. Raw grades retained separately. Revised development-discovered endpoint, not an unmodified official benchmark score; legacy clinical units remain unvalidated.',
        cost_scope='Logical episode calls/cost; exact cached episodes may replay, while receipt records refer to their first physical execution. Cleanup calls are counted separately.')
    (HERE/'results/summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    table='| Method | Split | State success | Original trace success | Model calls | Logical USD |\n|---|---|---:|---:|---:|---:|\n'
    for name,m in report['methods'].items():
        for split,row in m.items():table+=f"| {name} | {split} | {row['state_correct']}/{row['n']} | {row['trace_correct']}/{row['n']} | {row['model_calls']} | {row['logical_cost_usd']:.4f} |\n"
    for lang in ['en','zh']:
        path=HERE/f'RESULTS.{lang}.md';text=path.read_text()
        title='## Completed full task comparison' if lang=='en' else '## 完整任务比较已完成'
        extra='\n'+title+'\n\n'+table+'\n'
        extra+=('Every task is independently regraded against the original reference function, and every actual creation/readback/rollback/cleanup receipt is recounted. No grader exception is scored as a model error. Paired intervals, task-type breakdowns and accepted skill operations are in `results/summary.json`. These are one-seed task-level results; patient overlap prevents patient-generalization claims. Compiler repairs are fixed engineering, while language skills are the evolving artifacts.\n' if lang=='en' else '已逐任务独立调用原参考函数重评分，逐次核对实际创建/回读/回滚/清理回执；评分器异常不计为模型错误。配对区间、任务类型结果和技能接纳操作见 `results/summary.json`。这是一种子任务级结果，患者重叠不支持新患者泛化结论。编译器修复是固定工程改动，进化对象是语言技能。\n')
        if title not in text:path.write_text(text+extra)
    print(json.dumps({'status':'complete','methods':report['methods'],'paired':pairs}),flush=True)

if __name__=='__main__':main()
