"""Complete corrected local comparison after all six learning rounds freeze."""
import argparse,json,subprocess,time
from common import *
LLM=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.venv-llm/bin/python'
ANALYSIS=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.venv/bin/python'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--resume',action='store_true');args_cli=ap.parse_args()
    status_path=HERE/'results/pipeline_status.json';previous=json.loads(status_path.read_text()) if status_path.exists() else {}
    if previous.get('history') and not args_cli.resume:raise RuntimeError('Existing run detected; use --resume to preserve completed stages.')
    deadline=time.monotonic()+4*3600
    while not (PRIVATE/'test_freeze.json').exists():
        if time.monotonic()>deadline:raise RuntimeError('Learning did not finish; no test inference launched')
        time.sleep(15)
    stages=[(LLM,'declare_diagnostics.py',[]),(ANALYSIS,'learning_diagnostics.py',[]),
      (ANALYSIS,'training_trace_audit.py',[]),(ANALYSIS,'validator_replay.py',[]),(LLM,'run_final_suite.py',['--model','qwen']),
      (LLM,'trajectory_eval.py',[]),(LLM,'component_ablation.py',[]),(LLM,'catalogue_permutation.py',[]),
      (LLM,'evidence_ablation.py',[]),(ANALYSIS,'evidence_case_studies.py',[]),(LLM,'skemex_adapter.py',[]),(ANALYSIS,'skemex_state_audit.py',[]),(LLM,'run_final_suite.py',['--model','llama']),
      (LLM,'flame_adapter.py',[]),(LLM,'route_evidence_trial.py',[]),(ANALYSIS,'audit_results.py',[]),(ANALYSIS,'private_cases.py',[]),
      (ANALYSIS,'report.py',[]),(ANALYSIS,'make_figures.py',[]),(ANALYSIS,'provenance.py',[])]
    history=[x for x in previous.get('history',[]) if x['exit_code']==0] if args_cli.resume else []
    failed_attempts=previous.get('failed_attempts',[])+[x for x in previous.get('history',[]) if x['exit_code']!=0] if args_cli.resume else []
    completed={x['stage'] for x in history}
    for python,script,args in stages:
        name=Path(script).stem+('-'+args[-1] if args else '')
        if name in completed:continue
        start=time.time();log=PRIVATE/(name+'-pipeline.log')
        if log.exists():log.rename(PRIVATE/(name+f'-pipeline-before-{time.time_ns()}.log'))
        save(HERE/'results/pipeline_status.json',{'complete':False,'active':name,'history':history,'failed_attempts':failed_attempts})
        print(json.dumps({'start':name,'time':start}),flush=True)
        with log.open('w') as stream:r=subprocess.run([str(python),str(HERE/script),*args],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
        item={'stage':name,'exit_code':r.returncode,'seconds':time.time()-start};history.append(item)
        save(HERE/'results/pipeline_status.json',{'complete':False,'active':name,'history':history,'failed_attempts':failed_attempts});print(json.dumps(item),flush=True)
        if r.returncode:raise RuntimeError('Failed stage '+name+'; inspect restricted log')
    save(HERE/'results/pipeline_status.json',{'complete':True,'history':history,'failed_attempts':failed_attempts,'api_cost_usd':0,'paper_compile_and_git_sync_pending':True})
if __name__=='__main__':main()
