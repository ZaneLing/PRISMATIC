"""Freeze a development-motivated output-representation intervention before test."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path.home()/'Desktop/MedTreeBench/dataset/restricted'

def main():
    original=ROOT/'prismatic-v9/cases.json';private=ROOT/'prismatic-v15';private.mkdir(exist_ok=True)
    data=json.loads(original.read_text())
    for c in sum(data['blocks'],[])+data['validation']+data['guard']+data['test']:
        assert len(c['catalogue'])==20
        c['target_mask']=[int(k in c['target']) for k in c['catalogue']]
        c['messages'][0]['content']='You are an offline prescription research agent. For each of the 20 listed candidate order tools, decide whether it is likely to appear in the recorded prescription given the patient context. Return JSON only with exactly 20 integers in catalogue order (O1 through O20): {"include":[0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]}. Use 1 to include an order and 0 to exclude it. The example shows the required format, not an answer. Do not assume all candidates are needed.'
    (private/'cases.json').write_text(json.dumps(data)+'\n')
    protocol=json.loads((HERE.parent/'upgrade_v9/protocol.json').read_text())
    protocol.update(version='v0.15-binary-candidate-decisions',
        intervention='Exact 20-position include/exclude mask; all other QLoRA training settings and patient memberships match v9.',
        development_motivation='Guard target count averages 3.635 reachable drugs, whereas v9 adapted outputs select 14.57--18.71. Design frozen before v9 test results exist.',
        caveat='Equal steps/examples/output caps; binary targets contain more explicit negative decisions and a different number of target tokens. This is an output/supervision intervention, not a token-identical objective.',
        v9_test_results_present_at_design=(HERE.parent/'upgrade_v9/results/parameter_results.json').exists(),
        source_cases_sha256=hashlib.sha256(original.read_bytes()).hexdigest())
    assert not protocol['v9_test_results_present_at_design'],'Do not retroactively claim pre-test design'
    (HERE/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    (HERE/'results').mkdir(exist_ok=True)
    (HERE/'results/data_manifest.json').write_text((HERE.parent/'upgrade_v9/results/data_manifest.json').read_text())
    print(json.dumps({'status':'prepared','test_scores_not_yet_present':True,'training_cases':1800,'guard_cases':200,'test_cases':500}))

if __name__=='__main__':main()
