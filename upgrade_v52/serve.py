"""Run the compatible local RxRSIAgent without overwriting frozen study responses."""
import argparse
import actor
from common52 import *
from runtime_decoder import decode
from skills import execute,applies
def main():
 p=argparse.ArgumentParser();p.add_argument('--model',choices=['qwen','llama'],default='qwen');p.add_argument('--splits',nargs='+',default=['audit']);p.add_argument('--experimental-memory',action='store_true',help='Reproduce the audited memory despite observed omission regressions; not enabled by default.');args=p.parse_args()
 run=PRIVATE/'runtime';run.mkdir(exist_ok=True)
 for split in args.splits:
  link=run/(split+'.json')
  if not link.exists():link.symlink_to(PRIVATE/(split+'.json'))
 if not (run/'generation').exists():(run/'generation').symlink_to(PRIVATE/'generation',target_is_directory=True)
 actor.PRIVATE=run;actor.decode=decode;actor.run(args.model,args.splits)
 state=json.loads((PRIVATE/'qwen-compatible-52-states.json').read_text())[-1] if args.experimental_memory else []
 for split in args.splits:
  cases=json.loads((PRIVATE/(split+'.json')).read_text());rows=json.loads((run/(args.model+'-'+split+'.json')).read_text())
  final=[]
  for c,r in zip(cases,rows):
   assert c['case_id']==r['case_id'];orders=execute(c,r['orders'],state);lookup={key(o):i for i,o in c['catalogue'].items()}
   final.append({**r,'before_skill_orders':r['orders'],'before_skill_order_ids':r['order_ids'],'orders':orders,'order_ids':[lookup[key(o)] for o in orders],'active_skills':[s for s in state if applies(c,s)],'state_sha256':digest(state)})
  save(run/(args.model+'-'+split+('-experimental' if args.experimental_memory else '-initial')+'-final.json'),final)
 save(run/'manifest.json',{'runtime_sha256':sha(Path(__file__)),'decoder_sha256':sha(HERE/'runtime_decoder.py'),'state_sha256':digest(state),'model':args.model,'splits':args.splits})
 print('Compatible runtime outputs saved privately; frozen study files preserved.',flush=True)
if __name__=='__main__':main()
