"""Build local blinded review packages; annotation remains human supplied."""
import json,random,sys
from collections import Counter,defaultdict
from common53 import *
from programs import *
DIMENSIONS=['indication','effectiveness_for_goal','dose','route','frequency','duration','drug_drug_interaction','drug_disease_interaction','renal_hepatic_adjustment','unnecessary_duplication','monitoring','administration_feasibility']
def main():
    import joblib
    cs=json.loads((PRIVATE/'audit.json').read_text());out=json.loads((PRIVATE/'audit_outputs.json').read_text())['qwen']
    names=defaultdict(Counter)
    for c in joblib.load(SOURCE/'cases.joblib')['train']:
        for o in c['context']['prior_orders']:
            if o.get('drug_name'):names[o['drug_code']][o['drug_name']]+=1
    def readable(orders):return [dict(o,drug_name=names[o['drug_code']].most_common(1)[0][0] if names[o['drug_code']] else 'UNRESOLVED IDENTITY: '+o['drug_code']) for o in orders]
    ix=[]
    for multi in [False,True]:
        eligible=[i for i,c in enumerate(cs) if (len(c['context']['categories'])>=2)==multi]
        ix+=sorted(eligible,key=lambda i:digest(['v53-review',cs[i]['case_id']]))[:16]
    reviewdir=PRIVATE/'review';reviewdir.mkdir(exist_ok=True);keymap={};publiccounts=[]
    for rater in ['A','B']:
        rng=random.Random(53530+(rater=='B'));pack=[]
        for j,i in enumerate(ix):
            c=cs[i];rid=f'R{j+1:03d}';sources={'fixed_agent':out['fixed'][i],'conditional_agent':out['rxrsi_53'][i],'frozen_supervised':out['supervised_draft'][i],'recorded_future_orders':c['gold']}
            # Identical order sets are rated once and mapped back after blinding.
            unique={}
            for source,orders in sources.items():
                sig=digest(sorted(map(key,orders),key=str));unique.setdefault(sig,dict(orders=orders,sources=[]))['sources'].append(source)
            plans=list(unique.values());rng.shuffle(plans);rows=[]
            for k,p in enumerate(plans):
                pid=f'{rid}-{rater}-{k+1}';keymap[pid]=dict(case_id=c['case_id'],sources=p['sources'])
                rows.append(dict(plan_id=pid,orders=readable(p['orders']),order_reviews=[dict(order_index=n,ratings={d:None for d in DIMENSIONS},severity=None,evidence=None) for n in range(len(p['orders']))],missed_necessary_actions=None,unsupported_actions=None,overall_major_error=None,confidence=None))
            pack.append(dict(case=rid,decision_time='ICU hour6',context=c['context'],known_limitations=['No guaranteed allergy list, treatment intent, weight, active diagnosis status, cultures or complete medication history.','Recorded future orders may rely on later information. A missing target is not evidence that a treatment is clinically wrong.'],phase1_treatment_goals=None,phase1_required_information=None,plans=rows))
        save(reviewdir/('reviewer_'+rater+'.json'),dict(instructions='Complete phase1 before viewing/rating plans. Ratings: appropriate, marginal, inappropriate, unknown, not_applicable. Severity: none, minor, major, critical, unknown. Do not infer missing facts or trust a plan as GT. Return the completed JSON locally.',cases=pack))
        publiccounts.append(dict(rater=rater,cases=len(pack),plans=sum(len(x['plans']) for x in pack)))
    save(reviewdir/'BLINDING_KEY_DO_NOT_SHARE.json',keymap)
    # Separate rule inspection: no patient-level evidence is exported publicly.
    skills=[];seen=set()
    for seed in [53,153,253]:
        state=json.loads((PRIVATE/(str(seed)+'-states.json')).read_text())[-1]
        for card in state:
            rule={k:v for k,v in card.items() if k in ['op','drug_code','template','when','unless']};sig=digest(rule)
            if sig in seen:continue
            seen.add(sig);skills.append(dict(skill_id=sig,rule=rule,support=card['support'],counterexamples=card['counterexamples'],drug_name=names[card['drug_code']].most_common(1)[0][0] if names[card['drug_code']] else 'UNRESOLVED',clinical_indication_link=None,empirical_scope_plausible=None,missing_exception=None,source_support=None,unsafe_generalization=None,reviewer_decision=None))
    save(reviewdir/'skills_to_review.json',dict(instructions='These are statistical forecast rules, not established clinical recommendations. Review each independently; counterexample absence is a limitation.',skills=skills))
    # Diagnostic case studies, explicitly distinct from the random review sample.
    base=out['fixed'];final=out['rxrsi_53'];groups=defaultdict(list)
    for i,c in enumerate(cs):
        d=[a-b for a,b in zip(counts(final[i],c['gold'])[:3],counts(base[i],c['gold'])[:3])]
        group='tradeoff' if max(d)>0 else 'pareto_improvement' if min(d)<0 else 'unchanged_failure'
        if group!='unchanged_failure' or sum(counts(base[i],c['gold'])[:3])>0:groups[group].append((i,d))
    lines=['# Restricted diagnostic cases / 受限诊断病例','These are outcome-selected illustrations, not an unbiased clinical evaluation. 所有差异均相对记录GT，不代表临床对错。']
    for group,items in groups.items():
        for i,d in items[:3]:
            c=cs[i];lines+=['\n## '+group+' / '+c['case_id'][:10],'Δ(missed, extra, joint): '+str(d),'Observed diagnoses: '+'; '.join(c['context']['diagnoses'])]
            for label,orders in [('Before',base[i]),('After',final[i]),('Recorded target',c['gold'])]:
                lines+=['\n### '+label,'| Drug | Route | Dosage | Frequency |','|---|---|---|---|']
                lines+=['| '+' | '.join(str(o.get(f) or 'unknown').replace('|','/') for f in ['drug_name','route','dosage','frequency'])+' |' for o in readable(orders)]
    (PRIVATE/'CASE_STUDIES.md').write_text('\n'.join(lines)+'\n')
    save(HERE/'results/review_package.json',dict(random_cases=len(ix),strata={'one_system':16,'multiple_systems':16},reviewers=publiccounts,unique_skills=len(skills),completed_annotations=0,blinding_key_private=True,patient_content_exported=False,adapted_rubric_not_validated_scale=True))
if __name__=='__main__':main()
