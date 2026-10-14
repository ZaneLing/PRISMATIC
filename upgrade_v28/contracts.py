"""Task-text-only answer shape contracts; no benchmark IDs or answers."""
import datetime,math,re

def infer(instruction):
    text=instruction.lower().replace('’',"'")
    question=bool(re.match(r'\s*(what|which|find|tell|give)',text))
    if question and re.search(r'\bmrn\b',text) and 'name' in text:
        return {'kind':'identifier','instruction':'FINISH must contain exactly one identifier string, or the task-specified not-found string.'}
    if question and re.search(r'\b(age|value|level|cbg|glucose|average|measurement)\b',text):
        if re.search(r'\b(when|date|timestamp|what time)\b',text):
            return {'kind':'number_time','instruction':'Return exactly [numeric_value, ISO_timestamp] when a record is found, or [-1] if unavailable. Complete any requested write before FINISH.'}
        return {'kind':'number','instruction':'Return exactly one finite JSON number in FINISH([value]); do not add units, timestamps, objects or prose. Use the task missing-value sentinel when applicable.'}
    return {'kind':'list','instruction':'FINISH is a JSON list of only the values explicitly requested. Complete requested writes first. Do not add unsolicited prose.'}

def validate(answer,contract):
    if not isinstance(answer,list):return False
    numeric=lambda x:type(x) in (int,float) and math.isfinite(x)
    kind=contract['kind']
    if kind=='identifier':return len(answer)==1 and isinstance(answer[0],str)
    if kind=='number':return len(answer)==1 and numeric(answer[0])
    if kind=='number_time':
        if answer==[-1]:return True
        if len(answer)!=2 or not numeric(answer[0]) or not isinstance(answer[1],str):return False
        try:return datetime.datetime.fromisoformat(answer[1].replace('Z','+00:00')).tzinfo is not None
        except ValueError:return False
    return True
