"""Ground-truth-supervised prescription agent components.

The evolving policy selects drugs, the order memory supplies joint recorded
field templates, and a compiler emits complete structured research orders.
No current evaluation needs a human reviewer; missing GT fields stay unscored.
"""
import hashlib,json,re
from decimal import Decimal,InvalidOperation
from collections import Counter

CORE=('drug_name','route','dose_value','dose_unit')
FIELDS=CORE+('frequency_per_24h',)

def norm(value):
    if value is None:return None
    value=re.sub(r'\s+',' ',str(value).strip().lower())
    if value in ('','nan','none'):return None
    try:return format(Decimal(value).normalize(),'f')
    except InvalidOperation:return value

def hash_data(value):return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()

def record_order(row):
    return dict(zip(FIELDS,[norm(row[k]) for k in ['drug_key','route','dose_val_rx','dose_unit_rx','doses_per_24_hrs']]))

def key(order,fields=CORE):return tuple(order.get(f) for f in fields)

def saline(name):return bool(re.search(r'saline|sodium chloride|(^|[^a-z])nacl([^a-z]|$)|(^|[^a-z])ns([^a-z]|$)',name or ''))

def score(predictions,truth):
    drug_hits=drug_p=drug_g=core_hits=core_p=core_g=0
    field_hits=field_total=0;fluid_tp=fluid_fp=fluid_fn=0;empty=0
    for pred,gold in zip(predictions,truth):
        ps={o['drug_name'] for o in pred};gs={o['drug_name'] for o in gold}
        drug_hits+=len(ps&gs);drug_p+=len(ps);drug_g+=len(gs);empty+=int(not pred)
        pk={key(o) for o in pred if all(o.get(f) is not None for f in CORE)}
        gk={key(o) for o in gold if all(o.get(f) is not None for f in CORE)}
        core_hits+=len(pk&gk);core_p+=len(pk);core_g+=len(gk)
        # Field accuracy conditional on a correctly predicted drug name.
        for p in pred:
            same=[g for g in gold if g['drug_name']==p['drug_name']]
            if not same:continue
            for f in FIELDS[1:]:
                observed={g[f] for g in same if g[f] is not None}
                if observed:field_total+=1;field_hits+=int(p[f] in observed)
        pfluid=any(saline(x) for x in ps);gfluid=any(saline(x) for x in gs)
        fluid_tp+=pfluid and gfluid;fluid_fp+=pfluid and not gfluid;fluid_fn+=gfluid and not pfluid
    df=2*drug_hits/max(1,drug_p+drug_g);of=2*core_hits/max(1,core_p+core_g)
    return {'cases':len(truth),'drug_micro_f1':df,'drug_precision':drug_hits/max(1,drug_p),
      'drug_recall':drug_hits/max(1,drug_g),'core_order_micro_f1':of,
      'known_field_accuracy_given_correct_drug':field_hits/max(1,field_total),
      'known_fields_scored':field_total,'core_gold_orders':core_g,'core_predicted_orders':core_p,
      'saline_presence_f1':2*fluid_tp/max(1,2*fluid_tp+fluid_fp+fluid_fn),
      'mean_predicted_drugs':drug_p/max(1,len(truth)),'empty_fraction':empty/max(1,len(truth)),
      'promotion_score':.5*(df+of)}

def error_feedback(pred,gold,split):
    if split!='train':raise ValueError('Only training ground truth may update the agent')
    p={o['drug_name'] for o in pred};g={o['drug_name'] for o in gold}
    wrong=[]
    for name in p&g:
        po=[o for o in pred if o['drug_name']==name];go=[o for o in gold if o['drug_name']==name]
        for field in FIELDS[1:]:
            observed={o[field] for o in go if o[field] is not None}
            if observed and not any(o[field] in observed for o in po):wrong.append({'drug_name':name,'field':field})
    return {'missed_drugs':sorted(g-p),'extra_drugs':sorted(p-g),'field_errors':wrong,
            'reference_orders':gold,'feedback_source':'recorded_prescription_ground_truth'}

class OrderMemory:
    def __init__(self,orders):
        self.orders=orders;counts={};self.by_name=[]
        for episode in orders:
            index={}
            for order in episode:
                name=order['drug_name'];counts.setdefault(name,Counter())[key(order,FIELDS)]+=1
                index.setdefault(name,[]).append(order)
            self.by_name.append(index)
        self.defaults={name:dict(zip(FIELDS,counter.most_common(1)[0][0])) for name,counter in counts.items()}

    def synthesize(self,names,neighbors=(),similarities=(),conditional=True):
        output=[]
        for name in names:
            votes=Counter()
            if conditional:
                for i,s in zip(neighbors,similarities):
                    if s<=0:continue
                    for order in self.by_name[int(i)].get(name,[]):votes[key(order,FIELDS)]+=float(s)
            fields=dict(zip(FIELDS,votes.most_common(1)[0][0])) if votes else self.defaults[name].copy()
            fields.update(indication=None,fluid_purpose=None,volume_ml=None,rate_ml_h=None,
                          ingredient_id=None,duration=None,
                          provenance='similar_training_order' if votes else 'training_joint_template')
            output.append(fields)
        return output

def compile_selection(raw,candidates):
    """Tool-selected template IDs compile to fields; one invalid ID cannot erase others."""
    text=raw.strip()
    if text.startswith('```'):text=text.split('\n',1)[-1].rsplit('```',1)[0].strip()
    try:
        data=json.loads(text)
        if not isinstance(data,dict) or not isinstance(data.get('order_ids'),list):raise ValueError()
    except (ValueError,TypeError):return {'orders':[],'status':'invalid_json','problems':[]}
    ids=list(dict.fromkeys(i for i in data['order_ids'] if isinstance(i,str) and i in candidates))
    return {'orders':[candidates[i] for i in ids],
            'status':'valid' if len(ids)==len(data['order_ids']) else 'partial_repair',
            'problems':data.get('problems',[]),'questions':data.get('questions',[])}
