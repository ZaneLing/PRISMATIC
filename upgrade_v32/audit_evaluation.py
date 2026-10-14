"""Independent source, threshold, compiled-order and probability-receipt recount."""
import argparse,hashlib,json
from collections import defaultdict
from pathlib import Path
import numpy as np
from transformers import AutoTokenizer
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v32';MODEL=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/models/qwen3-4b-instruct-2507-4bit'
CORE=('drug_name','route','dose_value','dose_unit');FIELDS=CORE+('frequency_per_24h',)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(z):return hashlib.sha256(json.dumps(z,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def transformed(c,kind):
    orders=list(c['catalogue'].values());indices=list(range(20))
    if kind=='permuted':indices=sorted(indices,key=lambda i:hashlib.sha256(f'v31|0|0|evaluation|{c["case_id"]}|{i}'.encode()).hexdigest())
    elif kind=='reversed':indices=list(reversed(indices))
    else:assert kind=='ranked'
    catalogue={f'O{j+1}':orders[i] for j,i in enumerate(indices)};gold={o['drug_name'] for o in c['gold']};context=c['messages'][1]['content'].partition('\nCandidate order tools:\n')[0]
    text='\n'.join(f"O{j+1}: {orders[i]['drug_name'][:70]} | {orders[i]['route']} | {orders[i]['dose_value']} {orders[i]['dose_unit']} | original retrieval rank {i+1}" for j,i in enumerate(indices));system=c['messages'][0]['content']+' Original retrieval rank is provided on every candidate; smaller rank means a higher score from the same fixed retrieval tool. Return the inclusion mask in the displayed O1 through O20 order.'
    return {**c,'catalogue':catalogue,'original_rank_by_position':[i+1 for i in indices],'target_mask':[int(o['drug_name'] in gold) for o in catalogue.values()],'messages':[{'role':'system','content':system},{'role':'user','content':context+'\nCandidate order tools:\n'+text}]}
def metrics(pred,cases):
    assert len(pred)==len(cases);raw=[];values=[];people=defaultdict(list);field_correct=field_total=empty=0
    for i,(orders,c) in enumerate(zip(pred,cases)):
        assert all(o in c['catalogue'].values() for o in orders);p={o['drug_name'] for o in orders};g={o['drug_name'] for o in c['gold']};pc={tuple(o[k] for k in CORE) for o in orders if all(o.get(k) is not None for k in CORE)};gc={tuple(o[k] for k in CORE) for o in c['gold'] if all(o.get(k) is not None for k in CORE)};row=[len(p&g),len(p),len(g),len(pc&gc),len(pc),len(gc)];raw.append(row);values.append([2*row[0]/(row[1]+row[2]) if row[1]+row[2] else 1.,2*row[3]/(row[4]+row[5]) if row[4]+row[5] else 1.]);people[c['subject_hash']].append(i);empty+=not orders
        for order in orders:
            same=[o for o in c['gold'] if o['drug_name']==order['drug_name']]
            for key in FIELDS[1:]:
                observed={o[key] for o in same if o[key] is not None}
                if observed:field_total+=1;field_correct+=order[key] in observed
    raw=np.asarray(raw,dtype=float);values=np.asarray(values,dtype=float);counts=raw.sum(axis=0);keys=sorted(people);cluster_counts=np.asarray([raw[people[k]].sum(axis=0) for k in keys]);cluster_values=np.asarray([values[people[k]].mean(axis=0) for k in keys]);df=2*counts[0]/max(1,counts[1]+counts[2]);of=2*counts[3]/max(1,counts[4]+counts[5])
    result={'cases':len(cases),'drug_micro_f1':df,'drug_precision':counts[0]/max(1,counts[1]),'drug_recall':counts[0]/max(1,counts[2]),'core_order_micro_f1':of,'known_field_accuracy_given_correct_drug':field_correct/max(1,field_total),'known_fields_scored':field_total,'core_gold_orders':int(counts[5]),'core_predicted_orders':int(counts[4]),'mean_predicted_drugs':counts[1]/len(cases),'empty_fraction':empty/len(cases),'promotion_score':(df+of)/2,'patients':len(keys),'patient_drug_f1':cluster_values[:,0].mean(),'patient_order_f1':cluster_values[:,1].mean(),'compiler_schema_failures':0}
    return result,{'counts':cluster_counts,'values':cluster_values,'case_values':values,'keys':keys}
def probability_stats(prob,cases):
    p=np.asarray(prob).reshape(-1);y=np.asarray([c['target_mask'] for c in cases]).reshape(-1);positive=p[y==1];negative=p[y==0];auc=float(np.mean(positive[:,None]>negative[None,:])+.5*np.mean(positive[:,None]==negative[None,:])) if len(positive) and len(negative) else None;q=np.clip(p,1e-12,1-1e-12)
    return {'conditional_binary_bce':float(np.mean(-np.where(y==1,np.log(q),np.log1p(-q)))),'binary_auroc':auc,'brier':float(np.mean((y-p)**2)),'positive_slots':int(y.sum()),'total_slots':len(y),'mean_probability_one':float(p.mean()),'fraction_at_or_above_half':float(np.mean(p>=.5))}
def compile_orders(prob,cases,threshold):return [[order for order,p in zip(c['catalogue'].values(),vector) if p>=threshold] for vector,c in zip(prob,cases)]
def paired(parts):
    keys=parts[0][1]['keys'];assert all(e['keys']==keys for _,e in parts);draw=np.random.default_rng(32032).integers(0,len(keys),(4000,len(keys)));out={}
    for j,name in enumerate(['drug','core_order']):
        offset=j*3;bs_micro=np.zeros(4000);bs_patient=np.zeros(4000);observed_micro=observed_patient=0.;case_delta=np.zeros(len(parts[0][1]['case_values']))
        for w,e in parts:
            a=e['counts'][:,offset:offset+3];s=a.sum(axis=0);boot=a[draw].sum(axis=1);observed_micro+=w*2*s[0]/max(1,s[1]+s[2]);bs_micro+=w*2*boot[:,0]/np.maximum(1,boot[:,1]+boot[:,2]);observed_patient+=w*e['values'][:,j].mean();bs_patient+=w*e['values'][draw,j].mean(axis=1);case_delta+=w*e['case_values'][:,j]
        out[name]={'micro_f1_difference':float(observed_micro),'micro_f1_patient_ci95':np.quantile(bs_micro,[.025,.975]).tolist(),'patient_f1_difference':float(observed_patient),'patient_f1_ci95':np.quantile(bs_patient,[.025,.975]).tolist(),'positive_admission_contrast':int((case_delta>1e-12).sum()),'negative_admission_contrast':int((case_delta<-1e-12).sum()),'zero_admission_contrast':int((abs(case_delta)<=1e-12).sum()),'patients':len(keys),'admission_count_interpretation':'F1 fixes/regressions for two-state contrasts; algebraic interaction signs for four-state contrasts'}
    return out
def compare(actual,expected):
    if isinstance(expected,dict):
        assert set(actual)==set(expected),(set(actual),set(expected))
        for k,v in expected.items():compare(actual[k],v)
    elif isinstance(expected,(list,tuple)):
        assert len(actual)==len(expected)
        for a,e in zip(actual,expected):compare(a,e)
    elif isinstance(expected,(int,float,np.number)) and not isinstance(expected,bool):assert np.isfinite(actual) and abs(actual-expected)<1e-10,(actual,expected)
    else:assert actual==expected,(actual,expected)
def main(split):
    from evaluation_gate import check
    gate=check(split)
    if gate['status']!='open':raise RuntimeError('Repair recount remains closed: '+','.join(gate['pending']))
    path=HERE/f'results/{split}_summary.json';z=json.loads(path.read_text());lock=json.loads((PRIVATE/'evaluation_lock.json').read_text());assert z['evaluation_lock_sha256']==sha(PRIVATE/'evaluation_lock.json') and all(sha(ROOT/name)==h for name,h in lock['source_sha256'].items());assert sha(HERE/'results/training_audit.json')==lock['training_audit_sha256']
    source=PRIVATE.parent/'prismatic-v31/cases.json';assert sha(source)==lock['source_cases_sha256'];original=json.loads(source.read_text())['validation' if split=='proposal' else 'guard'];cases={kind:[transformed(c,kind) for c in original] for kind in z['views']};assert z['cases']==len(original) and z['patients']==len({c['subject_hash'] for c in original});config=json.loads((PRIVATE/'decision_config.json').read_text());assert sha(PRIVATE/'decision_config.json')==lock['decision_config_sha256'];tok=AutoTokenizer.from_pretrained(str(MODEL));probs={};receipt_count=0;unique_count=0;accounting={}
    assert z['state_versions']==lock['state_versions'];frozen=json.loads((PRIVATE/'frozen_thresholds.json').read_text());assert frozen['evaluation_lock_sha256']==sha(PRIVATE/'evaluation_lock.json') and not frozen['guard_inference_preceded_selection'] and frozen['proposal_summary_sha256']==sha(HERE/'results/proposal_summary.json')
    for name,version in lock['state_versions'].items():
        probs[name]={};signatures=set();seconds=0.;logical=0
        for kind,group in cases.items():
            bindings=PRIVATE/'inference'/name/'bindings'/f'{split}-{kind}.json';assert sha(bindings)==z['binding_sha256'][name][kind];rows=json.loads(bindings.read_text());assert len(rows)==len(group);vectors=[]
            for row,c in zip(rows,group):
                s=digest([version,digest(lock),c['messages'],'all_zero_include20',config]);rawfile=PRIVATE/'inference'/name/'raw'/f'{s}.json';assert row['case_id']==c['case_id'] and row['subject_hash']==c['subject_hash'] and row['signature']==s and row['raw_sha256']==sha(rawfile);r=json.loads(rawfile.read_text());assert r['signature']==s and r['state_version']==version and r['inference_source_signature']==digest(lock) and r['prompt_sha256']==digest(c['messages']) and row['conditional_probabilities']==r['conditional_probabilities']
                prefix=tok.apply_chat_template(c['messages'],add_generation_prompt=True,return_dict=False);sequence=tok.apply_chat_template(c['messages']+[{'role':'assistant','content':json.dumps({'include':[0]*20})}],return_dict=False);assert sequence[:len(prefix)]==prefix;positions=[len(prefix)+i for i in config['decision_offsets']];assert r['decision_positions']==positions and r['input_tokens']==len(sequence)-1 and all(sequence[i]==config['zero_token_id'] for i in positions)
                p=np.asarray(r['conditional_probabilities'],dtype=float);assert p.shape==(20,) and np.isfinite(p).all() and ((p>=0)&(p<=1)).all();vectors.append(p);receipt_count+=1;logical+=1
                if s not in signatures:signatures.add(s);seconds+=r['seconds_per_unique_prompt']
            probs[name][kind]=np.asarray(vectors)
        unique_count+=len(signatures);accounting[name]={'logical_case_views':logical,'unique_prompts_in_split':len(signatures),'forward_seconds_for_unique_prompts':seconds,'scope':'Stored unique-forward time excluding model loading/tokenization; not marginal new cost if a prompt is reused in another split.'}
    compare(z['inference_accounting'],accounting);selected=frozen['selection'];compare(z['selected_thresholds'],selected)
    if split=='proposal':
        recomputed={}
        for name,views in probs.items():
            curve=[];best=None
            for n in range(1,100):
                threshold=n/100.;m=[metrics(compile_orders(views[k],c,threshold),c)[0]['promotion_score'] for k,c in cases.items()];objective=sum(m)/len(m);curve.append({'threshold':threshold,'objective':objective})
                if best is None or objective>best['objective']+1e-12 or abs(objective-best['objective'])<=1e-12 and threshold>best['threshold']:best={'threshold':threshold,'objective':objective}
            recomputed[name]={**best,'grid_objectives':curve}
        compare(selected,recomputed)
    arms=json.loads((HERE/'protocol.json').read_text())['arms'];all_evidence={};all_pred={};endpoints={}
    for endpoint in ['fixed_half','proposal_calibrated']:
        endpoints[endpoint]={};all_evidence[endpoint]={};all_pred[endpoint]={}
        for kind,c in cases.items():
            scores={};ev={};pred={}
            for name,views in probs.items():
                threshold=.5 if endpoint=='fixed_half' else selected[name]['threshold'];pred[name]=compile_orders(views[kind],c,threshold);scores[name],ev[name]=metrics(pred[name],c);scores[name].update(threshold=threshold,**probability_stats(views[kind],c))
            for name,n in [('original_retrieval_top8',8),('all20_candidate_tools',20)]:pred[name]=[[o for o,r in zip(case['catalogue'].values(),case['original_rank_by_position']) if r<=n] for case in c];scores[name],ev[name]=metrics(pred[name],c)
            pairs={'zero_uniform_minus_teacher_uniform':[(1,'zero_uniform'),(-1,'teacher_uniform')],'zero_balanced_minus_teacher_balanced':[(1,'zero_balanced'),(-1,'teacher_balanced')],'zero_balanced_minus_zero_uniform':[(1,'zero_balanced'),(-1,'zero_uniform')],'teacher_balanced_minus_teacher_uniform':[(1,'teacher_balanced'),(-1,'teacher_uniform')],'prefix_by_balance_interaction':[(1,'zero_balanced'),(-1,'teacher_balanced'),(-1,'zero_uniform'),(1,'teacher_uniform')]}
            for arm in arms:
                for base in ['frozen_base','original_failed_adapter','original_retrieval_top8','all20_candidate_tools']:pairs[arm+'_minus_'+base]=[(1,arm),(-1,base)]
            endpoints[endpoint][kind]={'methods':scores,'contrasts':{name:paired([(w,ev[m]) for w,m in terms]) for name,terms in pairs.items()}};all_evidence[endpoint][kind]=ev;all_pred[endpoint][kind]=pred
    compare(z['endpoints'],endpoints);calibration={kind:{name:paired([(1,all_evidence['proposal_calibrated'][kind][name]),(-1,all_evidence['fixed_half'][kind][name])]) for name in probs} for kind in cases};compare(z['calibration_only_contrasts'],calibration);stable={}
    for endpoint,views in all_pred.items():
        stable[endpoint]={}
        for kind,pred in views.items():
            if kind=='ranked':continue
            stable[endpoint][kind]={}
            for name,second in pred.items():
                agreement=[];jac=[];nonempty=[]
                for a,b in zip(views['ranked'][name],second):
                    x={o['drug_name'] for o in a};y={o['drug_name'] for o in b};agreement.append(x==y);j=len(x&y)/len(x|y) if x or y else 1.;jac.append(j)
                    if x or y:nonempty.append(j)
                stable[endpoint][kind][name]={'cases':len(second),'drug_set_agreement':float(np.mean(agreement)),'mean_jaccard':float(np.mean(jac)),'nonempty_union_cases':len(nonempty),'nonempty_union_mean_jaccard':float(np.mean(nonempty)) if nonempty else None}
    compare(z['view_invariance'],stable);result={'status':'passed','split':split,'auditor_sha256':sha(Path(__file__)),'summary_sha256':sha(path),'evaluation_lock_sha256':sha(PRIVATE/'evaluation_lock.json'),'frozen_thresholds_sha256':sha(PRIVATE/'frozen_thresholds.json'),'case_probability_bindings_recounted':receipt_count,'unique_prompt_receipts_recounted':unique_count,'neural_states':len(probs),'methods_per_endpoint_and_view':len(probs)+2,'threshold_grid_points_recounted':99*len(probs) if split=='proposal' else 0,'scope':'Independent source/permutation/target, cached probability binding,99-point threshold, compiled-order, bootstrap and invariance recount. Optimizer and neural forward passes are not independently reexecuted.'};(HERE/f'results/{split}_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('split',choices=['proposal','guard']);args=parser.parse_args();main(args.split)
