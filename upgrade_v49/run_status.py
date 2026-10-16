"""Compact aggregate-only status for the ongoing local experiment."""
import json,re
from common import *
def main():
    pipeline=PRIVATE/'pipeline.log';events=[]
    if pipeline.exists():
        for line in pipeline.read_text().splitlines():
            try:events.append(json.loads(line))
            except ValueError:pass
    starts=[e for e in events if 'start' in e];stage=starts[-1]['start'] if starts else 'waiting'
    status_path=HERE/'results/pipeline_status.json';status=json.loads(status_path.read_text()) if status_path.exists() else {}
    result={'stage':stage,'complete':status.get('complete',False),'failed':bool(status.get('history') and status['history'][-1]['exit_code'])}
    log=PRIVATE/(stage+'-pipeline.log')
    if log.exists():
        lines=log.read_text().splitlines()[-25:]
        for line in reversed(lines):
            try:d=json.loads(line)
            except ValueError:continue
            if 'stage' in d:
                result['progress']=d;break
            if 'method' in d and 'metrics' in d:
                result['completed_method']=d['method'];result['drug_f1']=d['metrics']['drug_micro_f1'];break
        if any('Traceback (most recent call last)' in l for l in lines):result['traceback']=True
    print(json.dumps(result))
if __name__=='__main__':main()
