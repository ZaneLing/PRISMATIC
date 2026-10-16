"""Train-derived contrastive procedural memory with semantic applicability.

The model routes on observable question text, not gold/task metadata. A card
must carry training support and counterexamples; accepted routing must cite an
exact input span. Cards remain fallible experience, not clinical guidelines.
"""
import json
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'upgrade_v8'))
from public_client import request,json_object,digest
from agent import BASE,COT,MODULES
MODEL='deepseek/deepseek-v4.1-flash'


def call(messages,tokens,role):
    r=request(messages,MODEL,tokens,role=role)
    if r.get('error'):raise RuntimeError('Incomplete transport, no evaluation score')
    return r


def context(c):return c['dialogue']+'\n'+' | '.join(c['options'])


def checked_card(raw, allowed):
    if not isinstance(raw,dict):return None
    fields=('name','applies_when','exclude_when','procedure')
    if any(not isinstance(raw.get(k),str) or not raw[k].strip() for k in fields):return None
    pos=raw.get('support_ids',[]);neg=raw.get('counterexample_ids',[])
    if not isinstance(pos,list) or not isinstance(neg,list) or not pos or not neg:return None
    if not all(isinstance(x,str) and x in allowed for x in pos+neg):return None
    if set(pos)&set(neg):return None
    return {**{k:raw[k].strip()[:1000] for k in fields},'support_ids':pos[:2],
            'counterexample_ids':neg[:2]}


def propose(seen, baseline, old_cards, seed, round_index):
    by={r['case_id']:r for r in baseline}
    failures=[c for c in seen if by[c['id']]['prediction']!=c['gold']]
    successes=[c for c in seen if by[c['id']]['prediction']==c['gold']]
    failures=sorted(failures,key=lambda c:digest([seed,round_index,c['id']]))[:8]
    examples=[]
    if successes:
        vec=TfidfVectorizer(stop_words='english');x=vec.fit_transform([context(c) for c in successes])
    for c in failures:
        examples.append(c)
        if successes:
            sim=(vec.transform([context(c)])@x.T).toarray()[0]
            examples.append(successes[int(np.argmax(sim))])
    unique={c['id']:c for c in examples}
    feedback=[{'id':c['id'],'question':c['dialogue'],'options':c['options'],
               'reference_choice':c['gold'],'baseline_choice':by[c['id']]['prediction'],
               'baseline_evidence':by[c['id']].get('evidence','')} for c in unique.values()]
    prompt=('Learn up to two reusable procedural skill cards from the training errors and nearby successes below. '
        'Each card needs explicit observable applicability conditions, explicit exclusion conditions, a short decision procedure, '
        'at least one support case ID and a DIFFERENT counterexample case ID explaining when not to apply it. '
        'A counterexample is a nearby case where changing a correct decision by overgeneralizing this rule would be wrong. '
        'Learn how to compare evidence and options; do not invent drug facts, memorize answer letters or use benchmark positions. '
        'Training references are task feedback, not clinical authority. Exclusions must be meaningful, not merely "if irrelevant". '
        'Do not repeat existing cards. Return JSON {"cards":[{"name":"...","applies_when":"...",'
        '"exclude_when":"...","procedure":"...","support_ids":["..."],"counterexample_ids":["..."]}]}.\n'
        'Existing cards:\n'+json.dumps(old_cards)+'\nTraining feedback:\n'+json.dumps(feedback))
    receipt=call([{'role':'user','content':prompt}],2048,'contrastive_skill_proposer')
    parsed=json_object(receipt['raw']);raw=parsed.get('cards',[]) if isinstance(parsed,dict) else []
    cards=[]
    for c in raw[:2] if isinstance(raw,list) else []:
        card=checked_card(c,set(unique))
        if card and all(by[i]['prediction']!=unique[i]['gold'] for i in card['support_ids']) and all(by[i]['prediction']==unique[i]['gold'] for i in card['counterexample_ids']):cards.append(card)
    return old_cards+cards,receipt


class ScopedMemory:
    def __init__(self, train, cards):
        self.train={c['id']:c for c in train};self.cards=cards
        if cards:
            self.vector=TfidfVectorizer(stop_words='english')
            self.matrix=self.vector.fit_transform([c['name']+' '+c['applies_when']+' '+c['procedure'] for c in cards])

    def solve(self,c):
        receipts=[];selected=[];route_valid=True
        if self.cards:
            scores=(self.vector.transform([context(c)])@self.matrix.T).toarray()[0]
            candidates=[int(i) for i in np.argsort(-scores,kind='stable')[:4]]
            views=[{'card_index':i,**{k:self.cards[i][k] for k in ('name','applies_when','exclude_when','procedure')}} for i in candidates]
            routing=('Select at most TWO experience cards that apply to the CURRENT question. '
                'Check each positive condition and each exclusion. Do not apply a card if a required fact is absent or an exclusion holds. '
                'For each selected card quote an exact span from the current question/options that supports activation. '
                'Select none when inappropriate. Do not answer the medical question. Return JSON '
                '{"selected":[{"card_index":0,"input_quote":"exact span","exclusion_check":"why no exclusion holds"}]}.\nCards:\n'
                +json.dumps(views)+'\nCurrent question and options:\n'+context(c))
            r=call([{'role':'user','content':routing}],512,'semantic_skill_router');receipts.append(r)
            parsed=json_object(r['raw']);items=parsed.get('selected',[]) if isinstance(parsed,dict) else []
            if not isinstance(items,list):items=[];route_valid=False
            for item in items[:2]:
                if not isinstance(item,dict):continue
                index=item.get('card_index');quote=item.get('input_quote')
                if isinstance(index,int) and not isinstance(index,bool) and index in candidates and isinstance(quote,str) and len(quote.strip())>=8 and quote in context(c) and item.get('exclusion_check'):
                    if index not in selected:selected.append(index)
        memory=[]
        for index in selected:
            card=self.cards[index]
            view={k:card[k] for k in ('name','applies_when','exclude_when','procedure')}
            for field in ('support_ids','counterexample_ids'):
                view[field.replace('_ids','_examples')]=[{'question':self.train[i]['dialogue'],
                    'options':self.train[i]['options'],'reference_choice':self.train[i]['gold']} for i in card[field][:1]]
            memory.append(view)
        prompt=BASE+'\n'+COT+'\n'+'\n'.join(MODULES.values())
        if memory:prompt+='\nFallible training-derived procedures and contrasting examples. Verify applicability; they are not clinical guidance and cannot override current patient facts:\n'+json.dumps(memory)
        prompt+='\nCurrent question:\n'+c['dialogue']+'\nOptions:\n'+'\n'.join(f'{chr(65+i)}. {o}' for i,o in enumerate(c['options']))
        prompt+='\nReturn JSON only: {"evidence":"short decisive evidence","final":"one option letter"}.'
        r=call([{'role':'system','content':'Solve a verified public, fictional medication benchmark.'},
                {'role':'user','content':prompt}],1024,'scoped_memory_actor');receipts.append(r)
        parsed=json_object(r['raw']);answer=parsed.get('final') if isinstance(parsed,dict) else None
        answer=answer.strip().upper() if isinstance(answer,str) else None
        if answer not in [chr(65+i) for i in range(len(c['options']))]:answer=None
        return {'case_id':c['id'],'prediction':answer,'selected_card_indices':selected,
                'route_valid':route_valid,'calls':receipts,'state_sha256':digest(self.cards)}

    def batch(self,cases,workers=12):
        with ThreadPoolExecutor(max_workers=workers) as pool:return list(pool.map(self.solve,cases))
