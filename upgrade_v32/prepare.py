"""Verify and copy exactly the already observed400-example training repair set."""
import hashlib,json,sys
from pathlib import Path
from transformers import AutoTokenizer
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path.insert(0,str(ROOT/'upgrade_v31'))
from views import view,serialize
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v32';SOURCE=PRIVATE.parent/'prismatic-v31';MODEL=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/models/qwen3-4b-instruct-2507-4bit'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_once(p,content):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_text()==content
    else:p.write_text(content)
def main():
    spec=json.loads((HERE/'protocol.json').read_text());part=SOURCE/'seed42/permuted_uniform-round1';assert sha(part/'data/train.jsonl')==spec['source_training_sha256'] and sha(SOURCE/'cases.json')==spec['source_cases_sha256']
    data=json.loads((SOURCE/'cases.json').read_text());sample=json.loads((part/'sampling.json').read_text());lookup={c['case_id']:c for block in data['blocks'] for c in block};cases=[lookup[k] for k in sample['selected_case_ids']]
    expected=[serialize(view(c,'permuted',42,1,'train')) for c in cases];training=[json.loads(line) for line in (part/'data/train.jsonl').read_text().splitlines()];assert expected==training and len(cases)==400 and len({c['case_id'] for c in cases})==400
    validation=[serialize(view(c,'ranked')) for c in data['validation']];assert validation==[json.loads(line) for line in (part/'data/valid.jsonl').read_text().splitlines()]
    assert not {c['subject_hash'] for c in cases}&{c['subject_hash'] for c in data['validation']}
    tok=AutoTokenizer.from_pretrained(str(MODEL));zero=tok.encode('0',add_special_tokens=False);one=tok.encode('1',add_special_tokens=False);assert len(zero)==len(one)==1;bits=[zero[0],one[0]];offsets=None;lengths=[];positive=0
    for i,item in enumerate(training+validation):
        messages=item['messages'];target=json.loads(messages[-1]['content'])['include'];sequence=tok.apply_chat_template(messages,return_dict=False);prompt=tok.apply_chat_template(messages[:-1],add_generation_prompt=True,return_dict=False);assert sequence[:len(prompt)]==prompt
        pos=[j for j in range(len(prompt),len(sequence)) if sequence[j] in bits];assert len(pos)==20 and [bits.index(sequence[j]) for j in pos]==target
        relative=[j-len(prompt) for j in pos]
        if offsets is None:offsets=relative
        else:assert offsets==relative
        lengths.append(len(sequence))
        if i<400:positive+=sum(target)
    assert max(lengths)<=1536 and 0<positive<8000
    config={'decision_offsets':offsets,'zero_token_id':bits[0],'one_token_id':bits[1],'training_positive_weight':(8000-positive)/positive,'training_positive_slots':positive,'training_total_slots':8000}
    for name in ['train.jsonl','valid.jsonl']:write_once(PRIVATE/'data'/name,(part/'data'/name).read_text())
    write_once(PRIVATE/'proposal.json',json.dumps(data['validation'])+'\n');write_once(PRIVATE/'decision_config.json',json.dumps(config,indent=2)+'\n')
    out={'status':'passed','protocol_sha256':sha(HERE/'protocol.json'),'preparer_sha256':sha(Path(__file__)),'source_cases_sha256':sha(SOURCE/'cases.json'),'source_train_sha256':sha(part/'data/train.jsonl'),'source_valid_sha256':sha(part/'data/valid.jsonl'),'prepared_proposal_sha256':sha(PRIVATE/'proposal.json'),'decision_config_sha256':sha(PRIVATE/'decision_config.json'),'view_source_sha256':sha(ROOT/'upgrade_v31/views.py'),'training_examples':400,'proposal_examples':100,'training_patients':len({c['subject_hash'] for c in cases}),'proposal_patients':len({c['subject_hash'] for c in data['validation']}),'patient_overlap':0,'maximum_sequence_tokens':max(lengths),'target_truncations':0,'config':config,'guard_or_test_cases_copied':0,'api_calls':0,'fits':0}
    write_once(HERE/'results/data_audit.json',json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
