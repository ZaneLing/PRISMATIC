"""Resumable public-only API calls; credentials and headers are never logged."""
import hashlib,json,os,re,time,threading,urllib.request,urllib.error
from pathlib import Path
HERE=Path(__file__).resolve().parent
LOCAL=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/rxrsi-v8'
LOCAL.mkdir(exist_ok=True)
LOCK=threading.Lock()

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def credentials():
    key=os.getenv('OPENROUTER_API_KEY')
    if key:return key
    root=Path.home()/'Desktop/PRISMATIC'
    pattern=r'sk-or-v1-[A-Za-z0-9_-]+'
    for p in root.glob('*.md'):
        found=re.search(pattern,p.name)
        if found:return found.group(0).removesuffix('.md')
        if p.stat().st_size<100000:
            found=re.search(pattern,p.read_text(errors='ignore'))
            if found:return found.group(0)
    raise RuntimeError('OpenRouter credential unavailable; secret content withheld')

def json_object(raw):
    try:return json.loads(raw)
    except (ValueError,TypeError):
        m=re.search(r'\{.*\}',raw or '',re.S)
        if m:
            try:return json.loads(m.group())
            except ValueError:pass
    return {}

def request(messages,model,max_tokens,role='actor',temperature=0,cache_salt=None):
    body={'model':model,'messages':messages,'temperature':temperature,'max_tokens':max_tokens,
          'provider':{'zdr':True,'data_collection':'deny'}}
    if model.startswith('deepseek/'):body['reasoning']={'effort':'none'}
    signature=digest(body) if cache_salt is None else digest([body,cache_salt])
    folder=LOCAL/'cache';folder.mkdir(exist_ok=True);path=folder/(signature+'.json')
    if path.exists():
        # Compatibility with a concurrently finishing pre-atomic writer.
        for attempt in range(4):
            try:return json.loads(path.read_text())
            except json.JSONDecodeError:time.sleep(.05)
        raise RuntimeError('Incomplete response cache; raw file retained for inspection')
    key=credentials();last=None
    for retry in range(3):
        try:
            req=urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',data=json.dumps(body).encode(),
                headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','X-Title':'RxRSIAgent public benchmark evolution'},method='POST')
            start=time.time()
            with urllib.request.urlopen(req,timeout=90) as r:payload=json.load(r)
            usage=payload.get('usage') or {};content=payload.get('choices',[{}])[0].get('message',{}).get('content') or ''
            row={'raw':content,'input_tokens':usage.get('prompt_tokens',0),'output_tokens':usage.get('completion_tokens',0),
                 'cost_usd':usage.get('cost',0),'model_returned':payload.get('model'),
                 'seconds':time.time()-start,'request_sha256':signature,'role':role}
            with LOCK:
                temporary=path.with_suffix(f'.{os.getpid()}.{threading.get_ident()}.tmp')
                temporary.write_text(json.dumps(row,ensure_ascii=False)+'\n');os.replace(temporary,path)
                with (LOCAL/'usage.jsonl').open('a') as f:f.write(json.dumps({k:v for k,v in row.items() if k!='raw'})+'\n')
                total=sum(json.loads(s).get('cost_usd',0) or 0 for s in (LOCAL/'usage.jsonl').read_text().splitlines())
            if total>15:raise RuntimeError('Public evaluation cost cap reached; cached progress retained')
            return row
        except urllib.error.HTTPError as e:
            last='HTTP_'+str(e.code)
            if e.code in [400,401,402,403,404]:break
        except (urllib.error.URLError,TimeoutError,OSError) as e:last=type(e).__name__
        time.sleep(min(2**retry,8))
    return {'raw':'','error':last,'input_tokens':0,'output_tokens':0,'cost_usd':0,'request_sha256':signature,'role':role}
