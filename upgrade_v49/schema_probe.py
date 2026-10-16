"""Training-only controlled intervention on literal identifiers in format examples."""
import json,types,time,collections
from common import *
from local_backend import Backend
from audit_results import paired

REPLACEMENTS={
 'Return ONLY JSON {"facts":["F1","F2"]}.':'Return ONLY a JSON object with the single key facts, whose value is a list of observed F-identifier strings.',
 'Return ONLY JSON {"consider":["A1"],"avoid":["A2"]}.':'Return ONLY a JSON object with keys consider and avoid, each containing a list of catalogue identifier strings selected for this patient.',
 'Return ONLY JSON {"specialty":["A1"],"supportive":["A2"]}.':'Return ONLY a JSON object with keys specialty and supportive, each containing a list of catalogue identifier strings selected for this patient.',
 'Return ONLY JSON {"keep":["A1"],"flag_ids":["A2"]}.':'Return ONLY a JSON object with keys keep and flag_ids, each containing a list of catalogue identifier strings selected for this patient.',
 'Return ONLY JSON {"draft":["A1"]}.':'Return ONLY a JSON object with the single key draft, whose value is a list of catalogue identifier strings selected for this patient.',
 'Return ONLY JSON {"keep":["A1"],"avoid":["A2"]}.':'Return ONLY a JSON object with keys keep and avoid, each containing a list of catalogue identifier strings selected for this patient.',
 'Return only JSON {"order_ids":["A1",...]}. Use only actual catalogue IDs.':'Return only a JSON object with the single key order_ids, whose value is a list of actual catalogue identifier strings selected for this patient. Include all selected orders, or an empty list when none is selected.'}

def actor_style(style):
    source=(HERE/'actor.py').read_text()
    if style=='swapped_examples':source=source.replace('"A1"','"A23"').replace('"A2"','"A24"')
    elif style=='descriptive':
        for old,new in REPLACEMENTS.items():
            assert old in source,old
            source=source.replace(old,new)
    elif style!='original':raise ValueError(style)
    module=types.ModuleType('probe_actor_'+style);exec(compile(source,'probe_actor_'+style,'exec'),module.__dict__)
    return module

def main():
    cases=load_cases()['train'][:48]
    protocol={'stage':'training-only investigation after full-test non-transfer was observed','cases':48,
      'member_sha256':digest([c['case_id'] for c in cases]),'arms':['original','swapped_examples','descriptive'],
      'hypothesis':'format-example IDs can anchor order selection independently of patient evidence',
      'swapped_example_values':['A23','A24'],'output_caps':[128,128,96],
      'selection':'no swapped-ID variant may become the prescribing policy; it is a diagnostic of position shortcuts',
      'declared_unix':time.time(),'fresh_per_batch_generation':True,'api_cost_usd':0}
    save(HERE/'schema_probe_protocol.json',protocol)
    b=Backend();original_batch=b.batch;namespace=PRIVATE/'schema-probe-generation'/str(time.time_ns())
    def controlled(messages,cap=128,tag='infer'):
        b.cache=namespace/tag.replace('/','_');b.cache.mkdir(parents=True,exist_ok=True)
        return original_batch(messages,cap,tag)
    b.batch=controlled;results={};raw={}
    for style in protocol['arms']:
        a=actor_style(style);rows=a.run(b,cases,'rxrsi',{'cards':[]},'schema/'+style);raw[style]=rows
        save(PRIVATE/('schema-probe-'+style+'.json'),{'rows':rows})
        order=collections.Counter();facts=collections.Counter()
        for r in rows:order.update(r['order_ids']);facts.update(parse(r['plan']).get('facts',[]))
        results[style]={'metrics':metrics(rows,cases),'order_identifier_counts':dict(order),'fact_identifier_counts':dict(facts),
          'cases_selecting_A1':sum('A1' in r['order_ids'] for r in rows),'cases_selecting_A23':sum('A23' in r['order_ids'] for r in rows),
          'paired_to_original':paired(cases,raw['original'],rows)}
        save(HERE/'results/schema_probe.json',{'complete':False,'arms':results,'protocol_sha256':sha(HERE/'schema_probe_protocol.json')})
        print(json.dumps({'style':style,'metrics':results[style]['metrics']}),flush=True)
    save(HERE/'results/schema_probe.json',{'complete':True,'arms':results,'protocol_sha256':sha(HERE/'schema_probe_protocol.json')})
if __name__=='__main__':main()
