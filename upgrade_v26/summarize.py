"""Independently recount fixed development outputs and order equivariance."""
import hashlib,json,re
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v26'
FIELDS=['drug_name','route','dose_value','dose_unit']

def counts(pred,gold):
    p={o['drug_name'] for o in pred};g={o['drug_name'] for o in gold}
    a={tuple(o[k] for k in FIELDS) for o in pred if all(o.get(k) is not None for k in FIELDS)}
    b={tuple(o[k] for k in FIELDS) for o in gold if all(o.get(k) is not None for k in FIELDS)}
    return [len(p&g),len(p),len(g),len(a&b),len(a),len(b)]
def score(a):
    a=np.asarray(a).sum(axis=0);return np.array([2*a[0]/max(1,a[1]+a[2]),2*a[3]/max(1,a[4]+a[5])])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def key(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def main():
    protocol=json.loads((HERE/'protocol.json').read_text());progress=json.loads((HERE/'results/generation_progress.json').read_text());assert progress['status']=='complete'
    assert sha(PRIVATE/'guard_conditions.json')==protocol['prepared_guard_sha256'];data=json.loads((PRIVATE/'guard_conditions.json').read_text());original=data['original']
    _,groups=np.unique([c['subject_hash'] for c in original],return_inverse=True);n=int(groups.max()+1);summary={};pairs={};audits=[];controls={}
    for k in [8,20]:controls['direct_original_rank_top'+str(k)]=score([counts(list(c['catalogue'].values())[:k],c['gold']) for c in original]).tolist()
    rng=np.random.default_rng(42);draws=rng.integers(0,n,(1000,n))
    for model,conditions in progress['models'].items():
        summary[model]={};mats={};sets={}
        for condition,expected in conditions.items():
            cases=data[condition];rows=json.loads((PRIVATE/(model+'-'+condition+'.json')).read_text());assert [r['case_id'] for r in rows]==[c['case_id'] for c in cases]
            mat=[];display=original_prefix=valid=nontrivial=display_nontrivial=empty=invalid=0;sets[condition]=[]
            for row,c,base in zip(rows,cases,original):
                assert c['case_id']==base['case_id'] and c['gold']==base['gold']
                assert sorted(c['catalogue'].values(),key=lambda o:json.dumps(o,sort_keys=True))==sorted(base['catalogue'].values(),key=lambda o:json.dumps(o,sort_keys=True))
                sig=key([row['adapter_sha256'],c['messages'],128]);receipt_key=key([sig,c['case_id'],list(c['catalogue'].items())])
                p=PRIVATE/'inference-v2/cases'/(receipt_key+'.json');assert sha(p)==row['case_receipt_sha256']
                assert json.loads(p.read_text())=={k:v for k,v in row.items() if k!='case_receipt_sha256'}
                try:
                    bits=json.loads(re.sub(r'^<think>\s*</think>\s*','',row['raw'].strip(),count=1))['include']
                    assert isinstance(bits,list) and len(bits)==20 and all(type(b) is int and b in (0,1) for b in bits)
                    pred=[o for o,b in zip(c['catalogue'].values(),bits) if b];valid+=1
                    is_prefix=bits==[1]*sum(bits)+[0]*(20-sum(bits));display+=is_prefix
                    if 0<sum(bits)<20:nontrivial+=1;display_nontrivial+=is_prefix
                except (ValueError,TypeError,KeyError,AssertionError):pred=[];invalid+=1
                assert pred==row['orders'];s={o['drug_name'] for o in pred};sets[condition].append(s);empty+=not s
                original_prefix+=s=={o['drug_name'] for o in list(base['catalogue'].values())[:len(s)]}
                mat.append(counts(pred,c['gold']))
            a=np.asarray(mat);metrics=score(a);mats[condition]=a
            assert np.allclose(metrics,[expected['metrics']['drug_micro_f1'],expected['metrics']['core_order_micro_f1']],atol=1e-12,rtol=0)
            assert invalid==expected['metrics']['invalid_json']
            summary[model][condition]={'drug_order_f1':metrics.tolist(),'empty_fraction':empty/len(cases),'invalid':invalid,
              'display_prefix_fraction_among_valid':display/max(1,valid),'nontrivial_valid_masks':nontrivial,
              'display_prefix_fraction_nontrivial':display_nontrivial/max(1,nontrivial),'original_rank_prefix_fraction':original_prefix/len(cases)}
            audits.append({'model':model,'condition':condition,'independent_prediction_and_receipt_recount':'passed','cases':len(rows)})
        pairs[model]={}
        for left,right in [('ranked_explicit','original'),('permuted_rank_explicit','ranked_explicit'),('reversed_rank_explicit','ranked_explicit')]:
            clustered={}
            for kind in [left,right]:
                grouped=np.zeros((n,6));np.add.at(grouped,groups,mats[kind]);clustered[kind]=grouped
            bootstrap=np.array([score(clustered[left][ix])-score(clustered[right][ix]) for ix in draws])
            agreement=np.mean([a==b for a,b in zip(sets[left],sets[right])]);jac=np.mean([len(a&b)/len(a|b) if a|b else 1 for a,b in zip(sets[left],sets[right])])
            pairs[model][left+'__minus__'+right]={'drug_order_difference':(score(mats[left])-score(mats[right])).tolist(),
              'patient_ci95':np.quantile(bootstrap,[.025,.975],axis=0).tolist(),'same_medication_set_fraction':float(agreement),'mean_set_jaccard':float(jac)}
    result={'status':'complete','split':'development guard, previously used for checkpoint choice','cases':len(original),'patients':n,
      'methods':summary,'controls':controls,'paired':pairs,'audits':audits,'model_or_prompt_selection_performed':False,
      'claim_boundary':protocol['claim_boundary'],'interval_note':'1000 descriptive paired patient-cluster bootstrap draws, no multiplicity adjustment.'}
    (HERE/'results/summary.json').write_text(json.dumps(result,indent=2)+'\n')
    for lang in ['en','zh']:
        table='| Frozen method | Display condition | Drug F1 | Order F1 | Empty (%) | Invalid | Nontrivial display-prefix (%) |\n|---|---|---:|---:|---:|---:|---:|\n'
        for model,conditions in summary.items():
            for condition,v in conditions.items():table+=f"| {model} | {condition} | {v['drug_order_f1'][0]:.5f} | {v['drug_order_f1'][1]:.5f} | {100*v['empty_fraction']:.1f} | {v['invalid']} | {100*v['display_prefix_fraction_nontrivial']:.1f} |\n"
        paired='| Frozen method | Contrast | Drug/order Δ | Medication-set agreement (%) | Mean Jaccard |\n|---|---|---:|---:|---:|\n'
        for model,contrasts in pairs.items():
            for name,v in contrasts.items():paired+=f"| {model} | {name} | {v['drug_order_difference'][0]:+.5f}/{v['drug_order_difference'][1]:+.5f} | {100*v['same_medication_set_fraction']:.1f} | {v['mean_set_jaccard']:.3f} |\n"
        intro='''# v0.26 — Development diagnostic of candidate-position dependence

## Design

After v0.15 exposes prefix selection and collapsed checkpoints, freeze a diagnostic on its existing200-case/197-patient guard. No training or test case is evaluated. Keep the base model and both previously selected round2 adapters fixed. Compare fresh original prompts with ranked, deterministically permuted and reversed candidates. The latter three conditions explicitly retain each candidate's original retrieval rank, all drug/order fields and the same patient context; masks are interpreted in displayed order. Thus the reordering contrast does not silently remove the tool's rank information. The extra rank-prompt effect is measured separately against original prompts.

This is a post-test-motivated development sensitivity study, not untouched confirmation. It performs no checkpoint, prompt or model promotion. All generations stay local; duplicate inputs generate once and each case has an immutable output receipt.

## Fixed-method results

''' if lang=='en' else '''# v0.26：候选位置依赖的开发集诊断

## 设计

v0.15暴露前缀选择与检查点退化后，在其既有200例／197人guard上固定诊断；不评价训练/测试病例。冻结原模型及两臂已选第2轮适配器。比较重新生成的原提示，以及明确提供原始检索名次的顺序、确定性打乱、逆序候选。后三条件保留同样患者信息、全部药物/订单字段及原始名次，按展示顺序解释掩码，因此不是暗中删除有效排序信息。额外名次提示的影响另与原提示比较。

这是由已见测试诊断启发的开发敏感性实验，不是未触碰确认。没有重新训练，也不据此接纳任何模型、提示或检查点。生成全在本地，相同输入只生成一次，每例保存不可变回执。

## 冻结方法结果

'''
        controls_text='\nDirect original-rank controls (drug/order F1): '+', '.join(f'{k} {v[0]:.5f}/{v[1]:.5f}' for k,v in controls.items())+'.\n'
        tail=('\nAll predictions, candidate-set/GT equality and case-bound receipt hashes pass independent checks. Complete paired patient-cluster intervals are in `results/summary.json`. Order sensitivity does not by itself establish clinical reasoning or explain training collapse causally. No improvement or best-method claim follows from this diagnostic.\n' if lang=='en' else '\n全部预测、候选集合/GT一致性和逐例回执哈希通过独立核对。完整患者聚类配对区间见 `results/summary.json`。顺序敏感性不能直接证明临床思路，也不能单独解释训练退化的因果机制；本诊断不宣称改进或最佳方法。\n')
        (HERE/f'RESULTS.{lang}.md').write_text(intro+table+controls_text+'\n## Reordering contrasts / 重排比较\n\n'+paired+tail)
    print(json.dumps({'status':'complete','methods':summary,'paired':pairs}),flush=True)

if __name__=='__main__':main()
