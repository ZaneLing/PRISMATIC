"""Verify exact public benchmark coverage against pinned source records and saved answers."""
import csv,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
LOCAL=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local';RES=LOCAL/'resources'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def grade(rows,cases):
    byid={x['id']:x for x in cases};assert len(rows)==len(cases) and len({x['case_id'] for x in rows})==len(rows) and set(byid)=={x['case_id'] for x in rows}
    assert all(('gold' not in r or r['gold']==byid[r['case_id']]['gold']) and 'error' not in r for r in rows)
    assert all('correct' not in r or bool(r['correct'])==(r['prediction']==byid[r['case_id']]['gold']) for r in rows)
    return {'n':len(rows),'correct':sum(r['prediction']==byid[r['case_id']]['gold'] for r in rows),'invalid':sum(r['prediction'] not in ('A','B','C','D') for r in rows)}
def main():
    sources={};csvpath=RES/'rxqa/rxqa_openfda.csv';expected='52f99903426296c5576757aacaa500200616ecb501fb5d2b9d2c287ddfef8853';assert sha(csvpath)==expected;sources['rxqa_openfda.csv']=expected
    with csvpath.open(newline='') as stream:rows=list(csv.DictReader(stream))
    assert len(rows)==len({r['q_id'] for r in rows})==300
    rxqa=[]
    for row in sorted(rows,key=lambda x:hashlib.sha256(x['q_id'].encode()).hexdigest()):
        gold='ABCD'[int(row['correct_idx'])];assert row[gold]==row['correct']
        rxqa.append({'id':row['q_id'],'dialogue':row['question'],'options':[row[k] for k in 'ABCD'],'gold':gold})
    rxsafe=[];counts={}
    for kind,filename,key,expected in [('contraindication','RxSafeBench_Contradiction.json','Contradiction','e9e097408bbc9399768d88a04af3eac46674dac11af35251e51247453765446b'),('interaction','RxSafeBench_Interaction.json','interaction','d34cc05a98fe4120659b1a899d4cbf206e1a36cf0e1c4a3862efac0ea7f54fc9')]:
        path=RES/'RxSafeBench/data'/filename;assert sha(path)==expected;sources[filename]=expected
        raw=json.loads(path.read_text());unique={};total=0
        for category in raw:
            for item in category[key]:
                total+=1;identifier=hashlib.sha256((kind+item['dialogue']+item['med_true']).encode()).hexdigest()
                if identifier not in unique:unique[identifier]=(category,item)
        counts[kind]={'raw_records':total,'deduplicated_cases':len(unique),'duplicate_records':total-len(unique)}
        for rank,identifier in enumerate(sorted(unique)):
            category,item=unique[identifier];true_position=rank%3;others=[item['med_false'],item['med_not_related']]
            if int(identifier[0],16)%2:others=others[::-1]
            # The frozen conversion fills distractors by popping from the end.
            iterator=iter(reversed(others));options=[item['med_true'] if i==true_position else next(iterator) for i in range(3)]
            rxsafe.append({'id':identifier[:16],'type':kind,'indication':category.get('indication'),'dialogue':item['dialogue'],'options':options,'gold':'ABC'[true_position]})
    assert len(rxsafe)==2000 and len({c['id'] for c in rxsafe})==2000
    data_path=LOCAL/'rxrsi-v8/data.json';data=json.loads(data_path.read_text());assert len(data['transfer'])==300
    for got,expected in zip(data['transfer'],rxqa):assert all(got[k]==v for k,v in expected.items())
    combined=[c for rows in data['parts'].values() for c in rows];byid={c['id']:c for c in combined};assert len(combined)==len(byid)==2000
    for c in rxsafe:assert all(byid[c['id']][k]==v for k,v in c.items())
    memberships={k:{c['id'] for c in v} for k,v in data['parts'].items()};groups={k:{c['group_id'] for c in v} for k,v in data['parts'].items()}
    for i,k in enumerate(memberships):
        for j in list(memberships)[i+1:]:assert not memberships[k]&memberships[j] and not groups[k]&groups[j]
    manifest=json.loads((ROOT/'upgrade_v8/results/data_manifest.json').read_text());assert manifest['sample_sizes']=={k:len(v) for k,v in memberships.items()} and all(manifest['membership_sha256'][k]==digest(sorted(v)) for k,v in memberships.items())
    model='deepseek/deepseek-v4.1-flash';folder=ROOT/'upgrade_v3/results';scores={};prediction_sources={}
    for dataset,cases,file in [('rxsafebench',rxsafe,'openrouter_rxsafe_full_predictions.json'),('rxqa_openfda',rxqa,'openrouter_rxqa_full_predictions.json')]:
        path=folder/file;prediction_sources[file]=sha(path);rows=json.loads(path.read_text())[model];scores[dataset]={'direct':grade(rows,cases)}
        reported=json.loads((folder/file.replace('_predictions','')).read_text())['model_results'][model];assert reported['completed']==len(rows) and reported['correct']==scores[dataset]['direct']['correct']
    path=folder/'openrouter_rxsafe_full_harness_predictions.json';prediction_sources[path.name]=sha(path)
    original={r['case_id']:r for r in json.loads((folder/'openrouter_rxsafe_full_predictions.json').read_text())[model]}
    report=json.loads((folder/'openrouter_rxsafe_full_harness.json').read_text())['model_results'][model]['arms']
    for arm,rows in json.loads(path.read_text())[model].items():
        metric=grade(rows,rxsafe);assert all(r['initial']==original[r['case_id']]['prediction'] for r in rows);metric['fixes']=sum(r['prediction']==r['gold'] and original[r['case_id']]['prediction']!=r['gold'] for r in rows);metric['regressions']=sum(r['prediction']!=r['gold'] and original[r['case_id']]['prediction']==r['gold'] for r in rows)
        assert metric['correct']==report[arm]['correct'] and metric['fixes']==report[arm]['corrected'] and metric['regressions']==report[arm]['harmed'];scores['rxsafebench'][arm]=metric
    newer=LOCAL/'rxrsi-v8/grounded-grasp-v17-seed-42';transfer={}
    for method in ['cot','author_grasp','fixed_grounded','evolving_grounded']:
        path=newer/'round_evaluation'/(method+'-rxqa.json') if method in ['cot','author_grasp'] else newer/(method+'-rxqa.json');transfer[method]=grade(json.loads(path.read_text()),rxqa)
        prediction_sources[f'v17/{method}-rxqa.json']=sha(path)
    out={'status':'passed','auditor_sha256':sha(Path(__file__)),'public_source_sha256':sources,'public_data_snapshot_sha256':sha(data_path),'source_commits':{'rxqa':'203979bf928c1fe9e45aa89e2ed76c3d2a63b503','rxsafebench':'a25f9a1f173cf034b678c60f051901e86fbbbbb2'},'rxqa_openfda':{'public_rows':300,'unique_q_ids':300,'transferred_rows':300,'missing_or_added_rows':0,'full_public_component':True,'bnf_component_available':False,'label_and_option_identity_verified':True},'rxsafebench':{'counts':counts,'total_deduplicated':2000,'evolution_partition_counts':{k:len(v) for k,v in memberships.items()},'question_or_scenario_group_overlap':0,'full_deduplicated_historical_predictions':scores['rxsafebench'],'official_generation_protocol_equivalent':False},'historical_rxqa_direct':scores['rxqa_openfda'],'v17_complete_public_rxqa_predictions':transfer,'prediction_source_sha256':prediction_sources,'metadata_errata':['Historical v3 full-harness sample text says30+30, but all saved method outputs and source identities independently verify2000 cases. Preserve archived files; this audit supplies the correction.','RxQA300 is the entire released OpenFDA component, not a sampled portion of that public component; it does not cover the unreleased licensed BNF component.'],'new_model_calls':0,'scope':'Independent source reconstruction, complete-case identity/option/gold comparison and saved-prediction recount. No new method, clinical safety validation or official free-generation leaderboard equivalence.'}
    (HERE/'public_benchmark_coverage.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':'passed','rxqa_full_public':300,'rxsafebench_deduplicated':2000,'rxsafebench_raw':sum(v['raw_records'] for v in counts.values()),'historical_full_counts':scores,'v17_rxqa':transfer}))
if __name__=='__main__':main()
