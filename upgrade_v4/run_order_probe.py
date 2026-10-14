"""Generate research order drafts on ten fixed local cases, with one revision."""
import json,time,hashlib
from pathlib import Path
from mlx_lm import load,generate
from mlx_lm.sample_utils import make_sampler
from run_local_harness import PRIVATE,MODEL,HERE
from order_protocol import ALL_FIELDS

def run():
    cases=[json.loads(x) for x in (PRIVATE/'llm_inputs.jsonl').read_text().splitlines()][:10]
    dest=PRIVATE/'order_probe_predictions.jsonl'
    done={r['case_id']:r for r in map(json.loads,dest.read_text().splitlines())} if dest.exists() else {}
    expected=json.loads((HERE/'results/local_harness_results.json').read_text())['input_file_sha256']
    if hashlib.sha256((PRIVATE/'llm_inputs.jsonl').read_bytes()).hexdigest()!=expected:
        raise ValueError('Order-probe inputs differ from registered 50-case parent run')
    for r in done.values():
        if r['protocol_sha256']!=hashlib.sha256((HERE/'protocol.json').read_bytes()).hexdigest():
            raise ValueError('Protocol changed; use a new run identifier')
        if r['schema_sha256']!=hashlib.sha256((HERE/'order_schema.json').read_bytes()).hexdigest():
            raise ValueError('Schema changed; use a new run identifier')
    model,tok=load(str(MODEL));sampler=make_sampler(temp=0.)
    system=('Offline prescription-support research, not patient care. Produce at most TWO proposed orders, or abstain with orders:[]. '
      'Use only patient evidence E1 chiefcomplaint, E2 acuity, E3 home medication. Their entry availability is not fully verified. '
      'Allergy, weight, current renal function and validated DDI/renal knowledge are unavailable. '
      'Return ONLY JSON {"orders":[...]} with ALL these keys in every order: '+','.join(ALL_FIELDS)+'. '
      'drug_name,ingredient_id,formulation,concentration,atc4,dose_unit,route,frequency,duration,indication,fluid_purpose,reassessment '
      'are strings or null. dose_value,volume_ml,rate_ml_h are positive numbers or null. '
      'evidence_ids and uncertainty are arrays of strings. Do not invent ingredient IDs or unprovided measurements. '
      'Use null for unknown values and explain unknowns in uncertainty. Fluid purpose is resuscitation/maintenance/replacement/carrier/flush/unknown/null. '
      'Saline is not automatic: purpose, volume and rate must be supported; otherwise mark unknown. '
      'Do not call an order safe or ready to administer.')
    def infer(messages):
        p=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True);t=time.time()
        raw=generate(model,tok,prompt=p,max_tokens=640,sampler=sampler,verbose=False)
        return {'raw':raw,'tokens':len(tok.encode(raw)),'input_tokens':len(tok.encode(p)),'seconds':time.time()-t}
    for c in cases:
        if c['case_id'] in done:continue
        base=[{'role':'system','content':system},{'role':'user','content':json.dumps({
          'E1':c['chiefcomplaint'],'E2':c['acuity'],'E3':c['home_meds']})}]
        draft=infer(base)
        final=infer(base+[{'role':'assistant','content':draft['raw']},{'role':'user','content':json.dumps({
          'training_examples_not_patient_evidence':c['retrieved_cases'],
          'review':'Independently check every indication, missing dose/route/frequency and saline purpose/volume/rate. '
                   'Patient evidence IDs must refer to E1/E2/E3. Keep unsupported quantities null. '
                   'Do not infer clinical safety from absent knowledge. Revise once and return full JSON.'})}])
        r={'case_id':c['case_id'],'direct':draft,'retrieval_harness':final,
           'protocol_sha256':hashlib.sha256((HERE/'protocol.json').read_bytes()).hexdigest(),
           'schema_sha256':hashlib.sha256((HERE/'order_schema.json').read_bytes()).hexdigest()}
        with dest.open('a') as f:f.write(json.dumps(r)+'\n')
        print(json.dumps({'order_probe_completed':len(done)+1,'total':10}),flush=True);done[c['case_id']]=r

if __name__=='__main__':run()
