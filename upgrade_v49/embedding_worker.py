"""Local CPU MiniLM embeddings over complete text chunks; JSON-lines pipe only."""
import os,sys,json
os.environ['TOKENIZERS_PARALLELISM']='false'
from pathlib import Path
import torch
from transformers import AutoTokenizer,AutoModel
torch.set_num_threads(2)
path=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/models/minilm-l6-v2'
tok=AutoTokenizer.from_pretrained(str(path),local_files_only=True)
model=AutoModel.from_pretrained(str(path),local_files_only=True).eval()
def embed(texts):
    sequences=[];groups=[];lengths=[]
    for group,text in enumerate(texts):
        ids=tok.encode(text,add_special_tokens=False) or [tok.unk_token_id]
        for start in range(0,len(ids),254):
            part=ids[start:start+254];sequences.append([tok.cls_token_id]+part+[tok.sep_token_id]);groups.append(group);lengths.append(len(part))
    sums=torch.zeros((len(texts),384));weights=torch.zeros(len(texts))
    with torch.inference_mode():
        for lo in range(0,len(sequences),32):
            batch=tok.pad({'input_ids':sequences[lo:lo+32]},padding=True,return_tensors='pt')
            hidden=model(**batch).last_hidden_state;mask=batch['attention_mask'].unsqueeze(-1)
            pooled=(hidden*mask).sum(1)/mask.sum(1).clamp(min=1)
            for j,v in enumerate(pooled):
                i=lo+j;sums[groups[i]]+=v*lengths[i];weights[groups[i]]+=lengths[i]
    return torch.nn.functional.normalize(sums/weights[:,None].clamp(min=1),p=2,dim=1).tolist()
for line in sys.stdin:
    try:print(json.dumps({'vectors':embed(json.loads(line)['texts'])}),flush=True)
    except Exception as e:print(json.dumps({'error':type(e).__name__+': '+str(e)}),flush=True)
