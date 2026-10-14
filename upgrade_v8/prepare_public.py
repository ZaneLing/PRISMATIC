"""Verified public-only loader and scenario-group split; keep GT out of actor views."""
import json,sys
from pathlib import Path
from public_client import LOCAL,digest
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'upgrade_v2'))
from run_public_openrouter import verify_public_files,load_cases,SOURCE_COMMIT,PUBLIC_SHA256
from run_rxqa_openrouter import verify_public_file,load_cases as rxqa_load
RESOURCE=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources'

def run():
    source=RESOURCE/'RxSafeBench/data';verify_public_files(source);cases=load_cases(source,100000)
    parts={s:[] for s in ['train','proposal','guard','test']}
    group_sets={s:set() for s in parts}
    for c in cases:
        group=digest([c['type'],c.get('indication'),sorted(x.lower().strip() for x in c['options'])])
        bucket=int(digest(['rxrsi-v8-split',group])[:8],16)%100
        split='train' if bucket<30 else 'proposal' if bucket<40 else 'guard' if bucket<50 else 'test'
        c['group_id']=group;parts[split].append(c);group_sets[split].add(group)
    for a in parts:
        for b in parts:
            if a!=b:assert not group_sets[a]&group_sets[b]
    # Identical dialogue text must not cross a split either; remove all cross-split duplicates.
    owners={}
    for split,rows in parts.items():
        for c in rows:owners.setdefault(digest(c['dialogue'].strip().lower()),set()).add(split)
    excluded={k for k,v in owners.items() if len(v)>1}
    parts={s:[c for c in rows if digest(c['dialogue'].strip().lower()) not in excluded] for s,rows in parts.items()}
    path=RESOURCE/'rxqa/rxqa_openfda.csv';verify_public_file(path);transfer=rxqa_load(path,300)
    for c in transfer:c['dialogue']=c.pop('question')
    (LOCAL/'data.json').write_text(json.dumps({'parts':parts,'transfer':transfer},ensure_ascii=False)+'\n')
    report={'source_commit':SOURCE_COMMIT,'source_checksums':PUBLIC_SHA256,'total_deduplicated':len(cases),
      'sample_sizes':{s:len(v) for s,v in parts.items()},'cross_split_groups':0,'removed_cross_split_dialogues':len(excluded),
      'membership_sha256':{s:digest(sorted(c['id'] for c in rows)) for s,rows in parts.items()},'transfer_rxqa':300,
      'task_note':'Derived three-choice task; source-paper free generation scores are not same-protocol baselines.'}
    (HERE/'results/data_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

if __name__=='__main__':run()
