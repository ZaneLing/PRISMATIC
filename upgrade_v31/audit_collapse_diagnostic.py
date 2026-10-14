"""Independently recount saved diagnostic probabilities; no model reexecution."""
import hashlib,json,math
from pathlib import Path
import numpy as np
from sklearn.metrics import roc_auc_score,log_loss,brier_score_loss
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v31'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    path=HERE/'results/collapse_diagnostic.json';z=json.loads(path.read_text());assert z['status']=='executed';s=z['sources'];part=PRIVATE/'seed42/permuted_uniform-round1'
    assert s['protocol_sha256']==sha(HERE/'collapse_diagnostic_protocol.json') and s['script_sha256']==sha(HERE/'diagnose_collapse.py')
    assert s['source_training_sha256']==sha(part/'data/train.jsonl') and s['source_cases_sha256']==sha(PRIVATE/'cases.json') and s['adapter_sha256']==sha(part/'adapter/adapters.safetensors')
    model=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/models/qwen3-4b-instruct-2507-4bit';assert all(sha(model/name)==h for name,h in s['model_files_sha256'].items())
    directory=PRIVATE/'collapse-diagnostic';assert json.loads((directory/'lock.json').read_text())==s
    train=[json.loads(line) for line in (part/'data/train.jsonl').read_text().splitlines()];mask=[json.loads(x['messages'][-1]['content'])['include'] for x in train];prevalence=sum(map(sum,mask))/(len(mask)*20)
    stats={'examples':len(mask),'positive_slots':sum(map(sum,mask)),'total_slots':len(mask)*20,'prevalence':prevalence,'zero_target_examples':sum(sum(y)==0 for y in mask),'positive_by_position':[sum(y[i] for y in mask) for i in range(20)]};assert stats==z['training_label_statistics']
    examples=json.loads((PRIVATE/'cases.json').read_text())['validation'][:32];groups={'train_permuted':mask[:32]}
    for kind in ['ranked','permuted']:
        expected=[]
        for c in examples:
            orders=list(c['catalogue'].values());indices=list(range(20))
            if kind=='permuted':indices=sorted(indices,key=lambda i:hashlib.sha256(f'v31|0|0|evaluation|{c["case_id"]}|{i}'.encode()).hexdigest())
            gold={o['drug_name'] for o in c['gold']};expected.append([int(orders[i]['drug_name'] in gold) for i in indices])
        groups['proposal_'+kind]=expected
    records=0;max_delta=0.;receipts={}
    for state,conditions in z['states'].items():
        assert state in ['frozen_base','permuted_uniform_seed42_round1']
        for group,contexts in conditions.items():
            assert set(contexts)=={'teacher_forced_ground_truth_prefix','all_zero_prefix_without_ground_truth'}
            for context,reported in contexts.items():
                rows=[]
                for i,target in enumerate(groups[group]):
                    p=directory/f'{state}-{group}-{context}-{i}.json';r=json.loads(p.read_text());assert r['index']==i and r['target']==target and r['decision_tokens']==20 and r['prompt_target_alignment_verified']
                    assert len(r['probability_one'])==len(r['binary_token_mass'])==20
                    assert all(math.isfinite(v) and 0<=v<=1.00001 for v in r['probability_one']+r['binary_token_mass'])
                    rows.append(r);receipts[p.name]=sha(p);records+=1
                y=np.asarray([v for r in rows for v in r['target']]);p=np.asarray([v for r in rows for v in r['probability_one']]);clipped=np.clip(p,1e-12,1-1e-12)
                expected={'examples':len(rows),'slots':len(y),'positive_slots':int(y.sum()),'positive_prevalence':float(y.mean()),'conditional_binary_bce':float(log_loss(y,clipped,labels=[0,1])),'brier':float(brier_score_loss(y,p)),'auroc':float(roc_auc_score(y,p)),'mean_probability_one':float(p.mean()),'probability_one_sd':float(p.std()),'mean_probability_given_positive':float(p[y==1].mean()),'mean_probability_given_negative':float(p[y==0].mean()),'fraction_at_or_above_half':float((p>=.5).mean()),'constant_training_prevalence_bce':float(log_loss(y,np.full(len(y),prevalence),labels=[0,1])),'mean_binary_token_mass':float(np.mean([v for r in rows for v in r['binary_token_mass']]))}
                assert set(expected)==set(reported)
                for key,value in expected.items():delta=abs(value-reported[key]);assert delta<1e-10,(state,group,context,key,delta);max_delta=max(max_delta,delta)
    assert records==384
    for kind,r in z['cached_proposal'].items():
        p=part/f'proposal-{kind}.json';assert sha(p)==r['prediction_file_sha256'];rows=json.loads(p.read_text());assert len(rows)==r['examples']==100
        for row in rows:
            text=row['raw'].strip();prefix='<think>\n\n</think>';text=text[len(prefix):].strip() if text.startswith(prefix) else text
            assert json.loads(text)=={'include':[0]*20} and row['orders']==[] and row['status']=='valid'
    result={'status':'passed','source_report_sha256':sha(path),'auditor_sha256':sha(Path(__file__)),'saved_logit_examples_recounted':records,'cached_generation_masks_recounted':200,'maximum_metric_delta':max_delta,'private_probability_receipt_manifest_sha256':hashlib.sha256(json.dumps(receipts,sort_keys=True).encode()).hexdigest(),'scope':'Independent source/target reconstruction and sklearn metric recount of saved probabilities. Neural forward passes are not independently reexecuted; no optimizer refit, test score or clinical validation.'}
    (HERE/'results/collapse_diagnostic_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
