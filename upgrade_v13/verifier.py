"""Outcome-aware selection between an initial answer and a grounded revision."""
import re
import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import HashingVectorizer

NEGATIVE=re.compile(r'\b(not|avoid|contraindicated|inappropriate|unsafe|risk|worsen|interaction|caution)\b',re.I)
POSITIVE=re.compile(r'\b(indicated|preferred|appropriate|suitable|recommend|best|safe|effective|treat)\b',re.I)


def numeric(case,base,review):
    options=case['options'];b=base.get('prediction');r=review.get('prediction')
    features=[float(b==r),float(b not in ('A','B','C')),float(r not in ('A','B','C'))]
    for row in [base,review]:
        evidence=row.get('evidence','').lower()
        features += [min(len(evidence),2000)/2000,len(NEGATIVE.findall(evidence))/10,len(POSITIVE.findall(evidence))/10]
        for prediction in [b,r]:
            term=options[ord(prediction)-65].lower() if prediction in ('A','B','C') else ''
            matches=list(re.finditer(re.escape(term),evidence)) if term else []
            context=' '.join(evidence[max(0,m.start()-70):m.end()+70] for m in matches)
            features += [min(len(matches),10)/10,len(NEGATIVE.findall(context))/10,len(POSITIVE.findall(context))/10]
        features.append(row.get('label_evidence_trace',{}).get('missing_option_count',0)/3)
    return features


def features(cases,base,review,rich=True):
    """No gold or split membership is read; answer IDs are resolved via options."""
    numeric_x=csr_matrix(np.array([numeric(c,b,r) for c,b,r in zip(cases,base,review)]))
    if not rich:return numeric_x
    vec=HashingVectorizer(n_features=32768,alternate_sign=False,ngram_range=(1,2),stop_words='english',norm='l2')
    parts=[vec.transform([c['dialogue']+' Options: '+' | '.join(c['options']) for c in cases])]
    for rows in [base,review]:
        parts.append(vec.transform([r.get('evidence','') for r in rows]))
    return hstack(parts+[numeric_x],format='csr')


def selections(state,x,n):
    # Initialization is the development-selected balanced evidence review.
    if state is None:return np.ones(n,dtype=int)
    scores=state['model'].predict(x)
    assert np.isfinite(scores).all(),'Nonfinite verifier score must not become a silent base decision'
    return (scores>state['threshold']).astype(int)


def select_rows(base,review,selected):
    assert len(base)==len(review)==len(selected)
    assert [r['case_id'] for r in base]==[r['case_id'] for r in review]
    result=[]
    for b,r,s in zip(base,review,selected):
        row=dict(r if s else b)
        # Both responses must have been generated before an outcome verifier acts.
        # Review traces already include the initial draft cost.
        for key in ['input_tokens','output_tokens','cost_usd','seconds']:
            row[key]=r.get(key,0)
        row['verifier_selected']='review' if s else 'initial'
        result.append(row)
    return result
