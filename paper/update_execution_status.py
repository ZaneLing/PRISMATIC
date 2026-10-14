"""Publish operational status without credentials or account-level balances."""
import datetime,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    path=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/rxrsi-v8/api-unavailable.json'
    out={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'api':{'status':'available_no_local_block'},'local_training':'Independent local author-method and external-hospital queues are separate from the API.'}
    if path.exists():
        block=json.loads(path.read_text());code=block['http_status']
        affected=[]
        for version in (28,29,30):
            summary=HERE.parent/f'upgrade_v{version}/results/summary.json'
            if not summary.exists() or json.loads(summary.read_text()).get('status')!='complete':affected.append(f'v{version}')
        out['api']={'status':'waiting_for_credit' if code==402 else 'unavailable','http_status':code,'failure_time_utc':datetime.datetime.fromtimestamp(block['time'],datetime.timezone.utc).isoformat(),'affected_unfinished_studies':affected,'completed_artifacts_preserved':True,'incomplete_calls_scored':False}
    else:
        restored=path.parent/'api-restoration.json'
        if restored.exists():
            z=json.loads(restored.read_text())
            if z.get('actual_completion_succeeded'):
                out['api'].update(status='restored_actual_completion_verified',verified_at_utc=z['verified_at_utc'],model=z['model'],completed_artifacts_preserved=True,incomplete_calls_scored=False)
    (HERE/'execution_status.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
