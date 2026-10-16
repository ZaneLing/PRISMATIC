"""Complete corrected local comparison after all six learning rounds freeze."""
import json,subprocess,time
from common import *
LLM=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.venv-llm/bin/python'
ANALYSIS=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.venv/bin/python'
def main():
    deadline=time.monotonic()+4*3600
    while not (PRIVATE/'test_freeze.json').exists():
        if time.monotonic()>deadline:raise RuntimeError('Learning did not finish; no test inference launched')
        time.sleep(15)
    stages=[(LLM,'declare_diagnostics.py',[]),(LLM,'run_final_suite.py',['--model','qwen']),
      (LLM,'trajectory_eval.py',[]),(LLM,'component_ablation.py',[]),(LLM,'catalogue_permutation.py',[]),
      (LLM,'evidence_ablation.py',[]),(LLM,'skemex_adapter.py',[]),(LLM,'run_final_suite.py',['--model','llama']),
      (LLM,'flame_adapter.py',[]),(ANALYSIS,'audit_results.py',[]),(ANALYSIS,'private_cases.py',[]),
      (ANALYSIS,'report.py',[]),(ANALYSIS,'make_figures.py',[])]
    history=[]
    for python,script,args in stages:
        name=Path(script).stem+('-'+args[-1] if args else '');start=time.time();log=PRIVATE/(name+'-pipeline.log')
        save(HERE/'results/pipeline_status.json',{'complete':False,'active':name,'history':history})
        print(json.dumps({'start':name,'time':start}),flush=True)
        with log.open('w') as stream:r=subprocess.run([str(python),str(HERE/script),*args],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
        item={'stage':name,'exit_code':r.returncode,'seconds':time.time()-start};history.append(item)
        save(HERE/'results/pipeline_status.json',{'complete':False,'active':name,'history':history});print(json.dumps(item),flush=True)
        if r.returncode:raise RuntimeError('Failed stage '+name+'; inspect restricted log')
    save(HERE/'results/pipeline_status.json',{'complete':True,'history':history,'api_cost_usd':0,'paper_compile_and_git_sync_pending':True})
if __name__=='__main__':main()
