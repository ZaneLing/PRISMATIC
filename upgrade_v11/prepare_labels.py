"""Cache public option-drug labels from openFDA, without patient or gold data."""
import concurrent.futures,datetime,hashlib,json,re,threading,time,urllib.parse,urllib.request,urllib.error
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/rxrsi-v8'
LOCAL=ROOT.parent/'rxrsi-v11';LOCAL.mkdir(exist_ok=True)
LOCK=threading.Lock();NEXT=[0.]
FIELDS=['indications_and_usage','contraindications','drug_interactions','warnings_and_cautions','boxed_warning','use_in_specific_populations','dosage_and_administration','warnings']

def norm(s):return re.sub(r'[^a-z0-9]+',' ',s.lower()).strip()
def tokens(s):return set(norm(s).split())-{'and','with','the','for','in'}

def fetch(name):
    key=hashlib.sha256(name.encode()).hexdigest();path=LOCAL/'labels'/(key+'.json')
    if path.exists():return json.loads(path.read_text())
    quoted=name.replace('"',' ').replace('\\',' ')
    query=f'openfda.generic_name:"{quoted}" openfda.brand_name:"{quoted}"'
    url='https://api.fda.gov/drug/label.json?'+urllib.parse.urlencode({'search':query,'limit':5,'sort':'effective_time:desc'})
    result={'query_name':name,'request_url':url,'fetched_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'unavailable','label':None}
    with LOCK:
        wait=max(0,NEXT[0]-time.monotonic());NEXT[0]=max(NEXT[0],time.monotonic())+.28
    if wait:time.sleep(wait)
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'RxRSIAgent-research-label-retrieval'})
        with urllib.request.urlopen(req,timeout=35) as response:raw=response.read()
        data=json.loads(raw);matches=[]
        for label in data.get('results',[]):
            names=label.get('openfda',{}).get('generic_name',[])+label.get('openfda',{}).get('brand_name',[])
            if any(norm(name)==norm(n) or tokens(name)<=tokens(n) for n in names):matches.append(label)
        if matches:
            label=matches[0];result.update(status='matched',response_sha256=hashlib.sha256(raw).hexdigest(),label={k:label.get(k) for k in ['id','set_id','effective_time','openfda']+FIELDS})
        else:result['status']='no_verified_name_match'
    except urllib.error.HTTPError as e:result['status']='not_found' if e.code==404 else 'http_'+str(e.code)
    except (TimeoutError,urllib.error.URLError,OSError,ValueError) as e:result['status']=type(e).__name__
    path.write_text(json.dumps(result,ensure_ascii=False)+'\n');return result

def run():
    (LOCAL/'labels').mkdir(exist_ok=True)
    data=json.loads((ROOT/'data.json').read_text());names=sorted({x.lower().strip() for rows in data['parts'].values() for c in rows for x in c['options']})
    assert len(names)<=900,'Keep unauthenticated request count below the documented daily quota.'
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i,r in enumerate(pool.map(fetch,names),1):
            results.append(r)
            if i%50==0:print(json.dumps({'processed':i,'total':len(names),'matched':sum(x['status']=='matched' for x in results)}),flush=True)
    statuses={s:sum(x['status']==s for x in results) for s in sorted({x['status'] for x in results})}
    coverage={}
    indexed={r['query_name']:r for r in results}
    for split,cases in data['parts'].items():
        counts=[sum(indexed[o.lower().strip()]['status']=='matched' for o in c['options']) for c in cases]
        coverage[split]={'n':len(cases),'all_options_covered':sum(n==len(c['options']) for n,c in zip(counts,cases)),'any_option_covered':sum(n>0 for n in counts),'option_fraction':sum(counts)/sum(len(c['options']) for c in cases)}
    manifest={'source':'https://open.fda.gov/apis/drug/label/','query_names':len(names),'statuses':statuses,'coverage':coverage,
       'gold_used_for_retrieval':False,'patient_data_sent':False,'note':'Company-submitted drug-label records via openFDA; not a claim that FDA verified all label content or clinical correctness.',
       'source_manifest_sha256':hashlib.sha256(json.dumps([(r['query_name'],r.get('response_sha256'),r['status']) for r in results],sort_keys=True).encode()).hexdigest()}
    (LOCAL/'labels.json').write_text(json.dumps(indexed)+'\n');(HERE/'results').mkdir(exist_ok=True)
    (HERE/'results/label_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)

if __name__=='__main__':run()
