"""Finish predeclared diagnostics and regenerate reviewable artifacts."""
import json,subprocess,time
from common import *
LLM=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.venv-llm/bin/python'
ANALYSIS=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.venv/bin/python'
def main():
    deadline=time.monotonic()+12*3600
    while True:
        p=HERE/'results/pipeline_status.json';d=json.loads(p.read_text()) if p.exists() else {}
        if d.get('complete'):break
        if d.get('history') and d['history'][-1]['exit_code']:raise RuntimeError('Main suite failed; resolve it before diagnostics')
        if time.monotonic()>deadline:raise RuntimeError('Main suite did not finish within the monitoring window')
        time.sleep(15)
    stages=[(LLM,'upgrade_v49/component_ablation.py'),(LLM,'upgrade_v49/catalogue_permutation.py'),
      (ANALYSIS,'upgrade_v49/audit_results.py'),(ANALYSIS,'upgrade_v49/private_cases.py'),
      (ANALYSIS,'upgrade_v49/report.py'),(ANALYSIS,'upgrade_v49/make_figures.py'),(ANALYSIS,'paper/render_acl.py')]
    history=[]
    for python,script in stages:
        name=Path(script).stem;log=PRIVATE/(name+'-post.log');start=time.time()
        save(HERE/'results/delivery_status.json',{'complete':False,'active':name,'history':history})
        print(json.dumps({'start':name,'time':start}),flush=True)
        with log.open('w') as stream:r=subprocess.run([str(python),str(ROOT/script)],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
        record={'stage':name,'exit_code':r.returncode,'seconds':time.time()-start};history.append(record)
        save(HERE/'results/delivery_status.json',{'complete':False,'active':name,'history':history});print(json.dumps(record),flush=True)
        if r.returncode:raise RuntimeError('Failed final diagnostic/artifact stage: '+name)
    save(HERE/'results/delivery_status.json',{'complete':True,'history':history,'compile_and_git_sync_pending':True})
if __name__=='__main__':main()
