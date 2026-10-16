"""Offline label retrieval: exact cached product identity, with scope visible."""
import functools,json,re,heapq
from common import *
def normalize(s):return re.sub(r'[^a-z0-9]+',' ',s.lower()).strip()
@functools.lru_cache(maxsize=32768)
def sentence_words(s):return frozenset(normalize(s).split())
@functools.lru_cache(maxsize=4096)
def sentences(text):return tuple(s for s in re.split(r'(?<=[.!?])\s+',text) if 40<=len(s)<=900)
@functools.lru_cache(maxsize=1)
def bank():
    records={};folder=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/rxrsi-v45/full_labels'
    for p in sorted(folder.glob('*.json')):
        d=json.loads(p.read_text())
        for label in d.get('labels',[]):
            fd=label.get('openfda') or {};names=fd.get('generic_name',[])+fd.get('brand_name',[])
            if 'homeopathic' in json.dumps(fd).lower():continue
            if len(fd.get('substance_name',[]))>1:continue
            for name in names:records.setdefault(normalize(name),{})[label['id']]=label
    return records
def retrieve(c,plan):
    source=bank();words=set(normalize(c['input']+' '+plan).split());found={};matched=0
    for cid,o in c['catalogue'].items():
        labels=source.get(normalize(o['drug_name']),{})
        if labels:matched+=1
        for lid,label in labels.items():
            for sec in ['indications_and_usage','dosage_and_administration','contraindications']:
                text=' '.join(label.get(sec) or [])
                # Sentence boundaries retain qualifiers; no character-sliced partial sentence.
                for sentence in sentences(text):
                    overlap=len(words&sentence_words(sentence));candidate=(-overlap,cid,lid,sec,sentence,label.get('openfda',{}).get('route',[]))
                    if sentence not in found or candidate[:5]<found[sentence][:5]:found[sentence]=candidate
    top=heapq.nsmallest(2,found.values(),key=lambda x:x[:5])
    spans=[]
    for rank,cid,lid,sec,sentence,routes in top:
        spans.append({'order_id':cid,'source_id':lid,'section':sec,'source_route':routes,'quote':sentence})
    return {'matched_candidate_drugs':matched,'candidate_drugs':len(c['catalogue']),'spans':spans,
      'limits':'Exact cached product identity only. Retrieved text does not establish patient indication or correct dose; route compatibility is not inferred. No fresh network queries.'}
