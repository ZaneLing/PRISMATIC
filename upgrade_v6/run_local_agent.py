"""Local LLM planning + prescription compiler over evolved order tools.

Ground truth is never included in inference messages. It is read separately
for automatic scoring; validation decides whether LLM selection is promoted.
"""
import json,time
from pathlib import Path
from mlx_lm import load,generate
from mlx_lm.sample_utils import make_sampler
from rx_agent import compile_selection,score,hash_data

HERE=Path(__file__).resolve().parent
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v6'
MODEL=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/models/qwen3-4b-instruct-2507-4bit'

def run():
    model,tok=load(str(MODEL));sampler=make_sampler(temp=0.)
    fingerprint=hash_data({'source':Path(__file__).read_text(),'core':(HERE/'rx_agent.py').read_text()})
    report={}
    system=('You are RxRSIAgent, an offline prescription-generation research agent. '
      'Read the patient snapshot, identify treatment problems, and select a prescription from the available order tools. '
      'The catalogue contains joint drug/route/dose/unit/frequency templates learned from training prescriptions. '
      'These are statistical candidates, not patient-specific facts. Historical examples are not the target answer. '
      'Select likely recorded orders for this patient, considering primary treatment, medication continuity, '
      'and supportive/ancillary medicines or fluids when context supports them. Missing information does not '
      'mean all historical orders were absent. Do not select every candidate. Return JSON only: '
      '{"problems":["brief problem"],"order_ids":["O1"],"questions":["missing information"]}. '
      'Use only listed order IDs. The compiler will expand their structured fields. '
      'Do not invent a fluid purpose, infusion rate, allergy or renal measurement.')
    for split in ['val','test']:
        cases=[json.loads(x) for x in (PRIVATE/f'{split}_inputs.jsonl').read_text().splitlines()]
        labels=[json.loads(x)['orders'] for x in (PRIVATE/f'{split}_labels.jsonl').read_text().splitlines()]
        path=PRIVATE/f'{split}_agent_trace.jsonl';done={}
        if path.exists():
            for line in path.read_text().splitlines():
                r=json.loads(line);assert r['fingerprint']==fingerprint;done[r['case_id']]=r
        for case in cases:
            if case['case_id'] in done:
                assert done[case['case_id']]['input_sha256']==hash_data(case);continue
            arms={}
            for name,include_memory in [('catalogue_planner',False),('experience_planner',True)]:
                context={k:v for k,v in case.items() if k not in ['case_id','episode_memory']}
                if include_memory:context['episode_memory']=case['episode_memory']
                messages=[{'role':'system','content':system},{'role':'user','content':json.dumps(context)}]
                p=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True);start=time.time()
                raw=generate(model,tok,prompt=p,max_tokens=384,sampler=sampler,verbose=False)
                bundle=compile_selection(raw,case['candidate_orders'])
                arms[name]={'raw':raw,**bundle,'input_tokens':len(tok.encode(p)),
                     'output_tokens':len(tok.encode(raw)),'seconds':time.time()-start}
            arms['learned_policy']={'orders':[case['candidate_orders'][i] for i in case['policy_selected_ids']],
                     'status':'compiled','input_tokens':0,'output_tokens':0,'seconds':0}
            row={'case_id':case['case_id'],'input_sha256':hash_data(case),'fingerprint':fingerprint,'arms':arms,
                 'trace':['build_patient_state','retrieve_order_candidates','retrieve_training_experience',
                          'plan_problems_and_orders','compile_fields','record_missing_information','automatic_gt_evaluation_after_inference']}
            with path.open('a') as f:f.write(json.dumps(row)+'\n')
            done[case['case_id']]=row;print(json.dumps({'split':split,'completed':len(done),'total':len(cases)}),flush=True)
        rows=[done[c['case_id']] for c in cases]
        metrics={a:score([r['arms'][a]['orders'] for r in rows],labels) for a in rows[0]['arms']}
        if split=='val':
            # The simpler learned policy wins ties; no test-based selection.
            chosen=max(['learned_policy','catalogue_planner','experience_planner'],key=lambda a:metrics[a]['promotion_score'])
            gate={'chosen':chosen,'validation_scores':{a:m['promotion_score'] for a,m in metrics.items()},'fingerprint':fingerprint}
            (HERE/'results/agent_validation_gate.json').write_text(json.dumps(gate,indent=2)+'\n')
        metrics['rxrsi_selected']=metrics[chosen]
        report[split]={'metrics':metrics,'cost':{a:{k:sum(r['arms'][a][k] for r in rows) for k in ['input_tokens','output_tokens','seconds']} for a in rows[0]['arms']},
             'invalid_responses':{a:sum(r['arms'][a]['status']=='invalid_json' for r in rows) for a in rows[0]['arms']}}
    report.update(run_id='RxRSI-v6-local-agent-20-r1',fingerprint=fingerprint,validation_gate=gate,
       limits=['20-case developmental pilot, not the 4000-case policy experiment.',
               'LLM selects among learned templates; novel dose synthesis and LLM fine-tuning are not executed.',
               'Indication and fluid-role correctness are not scored without those GT fields.'])
    (HERE/'results/local_agent_results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'selected':chosen,'test':report['test']['metrics']}),flush=True)

if __name__=='__main__':run()
