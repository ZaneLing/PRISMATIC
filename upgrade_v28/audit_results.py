"""Independent reference, persisted-field and arithmetic recount of completed cells."""
import collections,contextlib,datetime,hashlib,io,json,sys,types
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path[:0]=[str(ROOT/'upgrade_v14'),str(ROOT/'upgrade_v19')]
from execution import grader_module,LOCAL,RESOURCE,BASE
from order_compiler import compile_order
from reference_compat import reference_view
from probe_fhir_state import total

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def statistics_audit(evidence):
    view=evidence['view'];pages=evidence['pages'];now=datetime.datetime.fromisoformat(view['task_clock']);records={};order=[]
    assert view['page_sha256']==[hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest() for p in pages]
    for page in pages:
        for entry in page.get('entry',[]):
            r=entry.get('resource',{})
            if r.get('resourceType')!='Observation':continue
            identifier=r.get('id') or hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()
            if identifier not in records:records[identifier]=r;order.append(identifier)
    assert len(records)==view['distinct_observations']
    selected=set()
    for g in view['numeric_groups']:
        ids=g['evidence_resource_ids'];assert len(ids)==len(set(ids)) and not selected.intersection(ids);selected.update(ids)
        source=[(i,records[i]) for i in order if i in ids];assert len(source)==g['count_available']
        for i,r in source:
            assert {k:r['valueQuantity'].get(k) for k in ['system','code','unit']}==g['unit']
            assert {'coding':sorted((r.get('code') or {}).get('coding',[]),key=lambda z:json.dumps(z,sort_keys=True)),'text':(r.get('code') or {}).get('text')}==g['observation_code']
        times=[datetime.datetime.fromisoformat(r['effectiveDateTime'].replace('Z','+00:00')) for i,r in source]
        assert all(t<=now for t in times);j=times.index(max(times));latest=source[j]
        assert g['latest']=={'resource_id':latest[0],'effectiveDateTime':latest[1]['effectiveDateTime'],'value':latest[1]['valueQuantity']['value']}
        ties=[r['valueQuantity']['value'] for (_,r),t in zip(source,times) if t==max(times)]
        assert g['latest_timestamp_tie_count']==len(ties) and g['latest_timestamp_distinct_values']==sorted(set(ties))
        recent=[(i,r,t) for (i,r),t in zip(source,times) if t>=now-datetime.timedelta(hours=24)]
        assert len(recent)==g['last24h']['count']
        if recent:
            assert abs(g['last24h']['mean']-np.mean([r['valueQuantity']['value'] for _,r,_ in recent]))<1e-10
            i,r,t=max(recent,key=lambda z:z[2]);assert g['last24h']['latest']=={'resource_id':i,'effectiveDateTime':r['effectiveDateTime'],'value':r['valueQuantity']['value']}
        else:assert g['last24h']['mean'] is None and g['last24h']['latest'] is None
    eligible=set()
    for identifier,r in records.items():
        q=r.get('valueQuantity') or {};v=q.get('value')
        if type(v) not in (int,float) or not np.isfinite(v) or not (q.get('code') or q.get('unit')):continue
        try:t=datetime.datetime.fromisoformat(r['effectiveDateTime'].replace('Z','+00:00'))
        except (KeyError,ValueError,AttributeError):continue
        if t.tzinfo is not None and t<=now:eligible.add(identifier)
    assert eligible==selected
    if view['complete_search']:
        assert not any(l.get('relation')=='next' for l in pages[-1].get('link',[]))
        assert sum(len(p.get('entry',[])) for p in pages)==pages[0].get('total',sum(len(p.get('entry',[])) for p in pages))

def audit_episode(row,case,grader):
    assert row['case_id']==case['id'] and not row['grader_errors'] and len(row['usage'])==row['model_calls']<=8
    assert all((u.get('output_tokens') or 0)<=512 for u in row['usage'])
    assert abs(sum(u.get('cost_usd') or 0 for u in row['usage'])-row['cost_usd'])<1e-12
    assert len(row['tools'])==row['tool_calls'];active=[];checks=[]
    for write in row['write_audits']:
        if write['create_status']!=201 or not isinstance(write['create_receipt'],dict) or not write['create_receipt'].get('id'):continue
        canonical=write['canonical_payload'];assert compile_order(write['submitted_payload'])[0]==canonical
        good=write['readback_status']==200 and all(write['readback'].get(k)==v for k,v in canonical.items() if k not in ['id','meta'])
        assert good==write['persisted'];checks.append(good)
        if write['rolled_back']:assert write['rollback_status'] in (200,204)
        else:active.append(good)
    assert checks==row['write_checks'] and active==row['active_post_checks'] and len(active)==row['writes']==len(row['cleanup_checks'])
    assert all(c['status'] in (200,204) for c in row['cleanup_checks'])
    projected,conversions=reference_view(row['live_trace']);assert projected==row['semantic_trace'] and conversions==row['reference_projection_audits']
    def grade(trace):
        if row['answer'] is None or row['status']!='completed':return False
        obj=types.SimpleNamespace(history=[types.SimpleNamespace(**m) for m in trace],result=row['answer'])
        with contextlib.redirect_stdout(io.StringIO()):return bool(getattr(grader,case['id'].split('_')[0])(case,obj,BASE))
    assert grade(row['original_trace'])==row['original_trace_correct'] and grade(row['live_trace'])==row['legacy_live_reference_correct']
    reference=grade(projected);assert reference==row['semantic_reference_correct'] and (reference and all(active))==row['live_execution_correct']
    for evidence in row['observation_audits']:statistics_audit(evidence)
    return int(row['live_execution_correct'])

def interval(delta,cases):
    units=[];patients=set();absent=0
    for c in cases:
        if c.get('eval_MRN'):
            patients.add(str(c['eval_MRN']));units.append('patient:'+str(c['eval_MRN']))
        else:
            # The two released validation name lookups deliberately describe
            # nonexistent patients. They have no patient to merge or invent.
            assert c['id'].startswith('task1_') and c['sol']==['Patient not found']
            units.append('negative_query:'+digest([c['instruction'],c.get('context','')]))
            absent+=1
    _,ix=np.unique(units,return_inverse=True);sizes=np.bincount(ix);sums=np.bincount(ix,weights=delta)
    rng=np.random.default_rng(42);draws=rng.integers(0,len(sizes),(4000,len(sizes)));values=sums[draws].sum(1)/sizes[draws].sum(1)
    return {'difference':float(np.mean(delta)),'patient_ci95':np.quantile(values,[.025,.975]).tolist(),'patients':len(patients),
      'negative_patient_queries':absent,'resampling_units':len(sizes),
      'cluster_note':'Explicit patient identities form clusters; declared nonexistent-patient queries are separate query units. This affects two validation cases, not either test split.'}

def main():
    source=json.loads((HERE/'results/method_results.json').read_text());lock=source['lock']
    assert lock['protocol_sha256']==sha(HERE/'protocol.json') and all(sha(ROOT/f)==h for f,h in lock['source_sha256'].items())
    grader=grader_module();result={'status':'partial','conditions':{},'paired':{},'source_lock':lock};correct={};cases_by_split={}
    for condition,config in source['conditions'].items():
        result['conditions'][condition]={'contract':config['contract'],'statistics':config['statistics'],'frozen_skills':config['frozen_skills'],'splits':{}}
        for split,summary in config['splits'].items():
            cases=json.loads((RESOURCE/'data/medagentbench'/('split_'+split+'.json')).read_text());cases_by_split[split]=cases
            rows=json.loads((LOCAL/'factorial-v28'/(condition+'-'+split+'.json')).read_text());assert [r['case_id'] for r in rows]==[c['id'] for c in cases]
            values=[];types_out=collections.defaultdict(list);raws=[]
            for item,case in zip(rows,cases):
                assert item['episode_digest']==digest([lock,condition,case['id']]);raw=json.loads((LOCAL/'factorial-v28/episodes'/(item['episode_digest']+'.json')).read_text())
                value=audit_episode(raw,case,grader);values.append(value);raws.append(raw);types_out[case['id'].split('_')[0]].append(value)
            assert sum(values)==summary['state_correct'] and len(values)==summary['n']
            assert sum(r['model_calls'] for r in raws)==summary['model_calls'] and sum(r['tool_calls'] for r in raws)==summary['http_calls_excluding_cleanup']
            assert sum(r['answer_shape_rejections'] for r in raws)==summary['answer_shape_rejections']
            correct[(condition,split)]=np.array(values)
            result['conditions'][condition]['splits'][split]={**summary,'independent_reference_field_and_arithmetic_audit':'passed',
              'task_types':{t:{'n':len(v),'correct':sum(v)} for t,v in types_out.items()},'output_tokens':sum(u.get('output_tokens') or 0 for r in raws for u in r['usage']),
              'input_tokens':sum(u.get('input_tokens') or 0 for r in raws for u in r['usage'])}
    for split,cases in cases_by_split.items():
        if sum((c,split) in correct for c in source['conditions'])!=8:continue
        get=lambda c,s,k:correct[(f'C{c}S{s}K{k}',split)]
        changes={'contract_main_effect':sum(get(1,s,k)-get(0,s,k) for s in [0,1] for k in [0,1])/4,
          'statistics_main_effect':sum(get(c,1,k)-get(c,0,k) for c in [0,1] for k in [0,1])/4,
          'frozen_skills_main_effect':sum(get(c,s,1)-get(c,s,0) for c in [0,1] for s in [0,1])/4,
          'skills_on_full_repair':get(1,1,1)-get(1,1,0),'full_repair_no_skills_minus_original_fixed':get(1,1,0)-get(0,0,0),
          'contract_statistics_interaction':sum(get(1,1,k)-get(1,0,k)-get(0,1,k)+get(0,0,k) for k in [0,1])/2}
        result['paired'][split]={name:interval(d,cases) for name,d in changes.items()}
    if source['status']=='execution_complete_pending_independent_audit':
        assert len(result['paired'])==3 and not list((LOCAL/'active').glob('*.json'))
        counts={r:total(r) for r in source['resource_counts_before']};assert counts==source['resource_counts_before']==source['resource_counts_after']
        result.update(status='complete',resource_counts_after=counts)
    result['claim_boundary']='Exploratory repeated-split engineering factorial, no new learning or test-based selection; descriptive patient-cluster intervals, no multiplicity correction. Logical model costs can include exact cached requests. Shared API ledger also includes concurrent studies and is not a per-study cost receipt.'
    (HERE/'results/summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'audited_cells':sum(len(x['splits']) for x in result['conditions'].values())}),flush=True)

if __name__=='__main__':main()
