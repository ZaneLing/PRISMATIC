"""Count materialized author-memory changes, separately from proposal intent."""
import json,re
from common import *
def snapshot(path):
    bodies={};meta={}
    for p in sorted(path.rglob('*.md')):
        if 'meta_memory' in p.parts:continue
        text=p.read_text();parts=re.split(r'^---\s*$',text,maxsplit=2,flags=re.M)
        body=parts[2].strip() if len(parts)==3 else text.strip()
        name=str(p.relative_to(path));bodies[name]=digest(body);meta[name]=sha(p)
    index=next(iter(path.rglob('utility_index.json')),None)
    utilities=json.loads(index.read_text()) if index else {}
    return bodies,meta,utilities

def main():
    root=PRIVATE/'skemex-round-snapshots';previous=snapshot(root/'0');out=[]
    out.append({'round':0,'materialized_nonmeta_files':len(previous[0]),'new_files':0,'removed_files':0,'changed_procedure_bodies':0,'changed_existing_utility_entries':0,'body_state_sha256':digest(previous[0])})
    for rnd in range(1,7):
        if not (root/str(rnd)).exists():break
        current=snapshot(root/str(rnd));old,oldmeta,oldu=previous;new,meta,utility=current
        out.append({'round':rnd,'materialized_nonmeta_files':len(new),'new_files':len(set(new)-set(old)),
          'removed_files':len(set(old)-set(new)),
          'changed_procedure_bodies':sum(new[k]!=old[k] for k in set(new)&set(old)),
          'changed_files_including_metadata':sum(meta[k]!=oldmeta[k] for k in set(meta)&set(oldmeta)),
          'changed_existing_utility_entries':sum(utility[k]!=oldu[k] for k in set(utility)&set(oldu)),
          'body_state_sha256':digest(new)})
        previous=current
    save(HERE/'results/skemex_state_audit.json',{'complete':len(out)==7,'rounds':out,
       'source':'private per-round snapshots; compare actual procedure bodies and utility entries, not CREATE/PATCH intents',
       'weights_updated':False,'executable_tool_code_learned':False,'patient_content_published':False})
    print(json.dumps(out))
if __name__=='__main__':main()
