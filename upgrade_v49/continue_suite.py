"""Sequential local runner; no network inference and no silent stage skipping."""
import argparse,json,subprocess,time,sys,os
from common import *
LLM=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.venv-llm/bin/python'
ANALYSIS=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.venv/bin/python'
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--wait-for-development',action='store_true');a=parser.parse_args()
    if a.wait_for_development:
        deadline=time.monotonic()+7200
        while not (HERE/'test_freeze_scope.json').exists():
            if time.monotonic()>deadline:raise RuntimeError('Development did not finish; no evaluation launched')
            time.sleep(15)
    stages=[(LLM,'convert_flame.py',[]),(LLM,'run_final_suite.py',['--model','qwen']),
      (LLM,'skemex_adapter.py',[]),(LLM,'run_final_suite.py',['--model','llama']),
      (LLM,'trajectory_eval.py',[]),(LLM,'flame_adapter.py',[]),(LLM,'evidence_ablation.py',[]),
      (ANALYSIS,'audit_results.py',[]),(ANALYSIS,'report.py',[])]
    history=[]
    for python,script,args in stages:
        name=script.removesuffix('.py');start=time.time();log=PRIVATE/(name+'-pipeline.log')
        print(json.dumps({'start':name,'time':start}),flush=True)
        with log.open('w') as stream:
            result=subprocess.run([str(python),str(HERE/script),*args],cwd=str(ROOT),stdout=stream,stderr=subprocess.STDOUT)
        record={'stage':name,'exit_code':result.returncode,'seconds':time.time()-start};history.append(record)
        save(HERE/'results/pipeline_status.json',{'history':history,'complete':False,'api_cost_usd':0})
        print(json.dumps(record),flush=True)
        if result.returncode:raise RuntimeError('Failed stage '+name+'; inspect the local restricted log')
    save(HERE/'results/pipeline_status.json',{'history':history,'complete':True,'api_cost_usd':0})
if __name__=='__main__':main()
