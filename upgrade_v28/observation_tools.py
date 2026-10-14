"""Arithmetic views of real Observation pages, with explicit provenance/limits."""
import collections,datetime,hashlib,json,math,urllib.parse

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
def time_value(value):
    if not isinstance(value,str):return None
    try:
        d=datetime.datetime.fromisoformat(value.replace('Z','+00:00'))
        return d if d.tzinfo is not None else None
    except ValueError:return None

def summarize(pages,clock,complete):
    now=time_value(clock);assert now is not None
    groups=collections.defaultdict(list);ignored=collections.Counter();seen=set();receipts=[]
    for page in pages:
        receipts.append(digest(page))
        for entry in page.get('entry',[]):
            record=entry.get('resource',{})
            if record.get('resourceType')!='Observation':ignored['non_observation']+=1;continue
            identity=record.get('id') or digest(record)
            if identity in seen:ignored['duplicate_resource']+=1;continue
            seen.add(identity);quantity=record.get('valueQuantity') or {};value=quantity.get('value')
            if type(value) not in (int,float) or not math.isfinite(value):ignored['non_numeric']+=1;continue
            dt=time_value(record.get('effectiveDateTime'))
            if dt is None:ignored['missing_or_unzoned_time']+=1;continue
            if dt>now:ignored['future_measurement']+=1;continue
            code=record.get('code') or {}
            code_key=json.dumps({'coding':sorted(code.get('coding',[]),key=lambda x:json.dumps(x,sort_keys=True)),'text':code.get('text')},sort_keys=True)
            unit_key=json.dumps({k:quantity.get(k) for k in ['system','code','unit']},sort_keys=True)
            if not quantity.get('code') and not quantity.get('unit'):ignored['missing_unit']+=1;continue
            groups[(code_key,unit_key)].append({'resource_id':identity,'effectiveDateTime':record['effectiveDateTime'],'value':value})
    out=[]
    for (code,unit),values in sorted(groups.items()):
        values.sort(key=lambda x:(time_value(x['effectiveDateTime']),x['resource_id']))
        recent=[v for v in values if time_value(v['effectiveDateTime'])>=now-datetime.timedelta(hours=24)]
        out.append({'observation_code':json.loads(code),'unit':json.loads(unit),'count_available':len(values),'latest':values[-1],
          'last24h':{'count':len(recent),'mean':sum(x['value'] for x in recent)/len(recent) if recent else None,
             'latest':recent[-1] if recent else None},'evidence_resource_ids':[v['resource_id'] for v in values]})
    return {'task_clock':clock,'complete_search':complete,'pages':len(pages),'page_sha256':receipts,'distinct_observations':len(seen),
      'omitted':dict(ignored),'numeric_groups':out,'limits':'Statistics refer only to this query and successfully retrieved pages. Incomplete searches cannot establish absence or a globally latest measurement. Codes/units are not clinically harmonized.'}

def retrieve(path,http_request,base,clock,max_pages=5):
    parts=urllib.parse.urlsplit(path);query=urllib.parse.parse_qsl(parts.query,keep_blank_values=True)
    if parts.path!='Observation' or not any(k=='patient' and v for k,v in query) or any(k=='_summary' for k,v in query):
        status,payload=http_request('GET',path);return status,payload,[{'path':path,'status':status}],None
    query=[(k,v) for k,v in query if k!='_count']+[('_count','5000')]
    next_path='Observation?'+urllib.parse.urlencode(query);pages=[];calls=[];visited=set();complete=False
    for page_index in range(max_pages):
        if next_path in visited:break
        visited.add(next_path);status,payload=http_request('GET',next_path);calls.append({'path':next_path,'status':status})
        if status!=200 or not isinstance(payload,dict) or payload.get('resourceType')!='Bundle':
            if not pages:return status,payload,calls,None
            break
        pages.append(payload);next_url=next((x.get('url') for x in payload.get('link',[]) if x.get('relation')=='next'),None)
        if not next_url:
            complete=sum(len(p.get('entry',[])) for p in pages)==pages[0].get('total',sum(len(p.get('entry',[])) for p in pages));break
        # A server paging URL must remain on the same local FHIR origin/base.
        if not next_url.startswith(base):break
        next_path=next_url[len(base):]
        if '..' in next_path or '://' in next_path:break
    view=summarize(pages,clock,complete)
    return 200,{'resourceType':'ObservationStatistics','source_query':path,**view},calls,{'source_query':path,'pages':pages,'view':view}
