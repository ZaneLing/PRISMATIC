"""Public label evidence retrieval with explicit missingness and source provenance."""
import json,re,sys
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'upgrade_v8'))
from agent import Agent
from prepare_labels import LOCAL,FIELDS

PROFILES={
 'balanced':{'indications_and_usage':1.2,'contraindications':1.2,'drug_interactions':1.2,'warnings_and_cautions':1.,'boxed_warning':1.,'use_in_specific_populations':1.,'warnings':1.},
 'safety':{'indications_and_usage':.65,'contraindications':1.7,'drug_interactions':1.7,'warnings_and_cautions':1.1,'boxed_warning':1.4,'use_in_specific_populations':1.2,'warnings':1.},
 'indication':{'indications_and_usage':2.0,'contraindications':1.0,'drug_interactions':1.0,'warnings_and_cautions':.6,'boxed_warning':.8,'use_in_specific_populations':.7,'warnings':.6}}

class LabelEvidence:
    def __init__(self):
        self.labels=json.loads((LOCAL/'labels.json').read_text());self.chunks=[];self.by_name={}
        for name,record in sorted(self.labels.items()):
            if record['status']!='matched':continue
            label=record['label'];indices=[]
            for field in FIELDS:
                if field=='dosage_and_administration':continue
                values=label.get(field) or []
                if isinstance(values,str):values=[values]
                for paragraph in values:
                    # Keep exact source text, with bounded contiguous excerpts.
                    for start in range(0,min(len(paragraph),30000),500):
                        excerpt=paragraph[start:start+650]
                        if len(excerpt.strip())<20:continue
                        indices.append(len(self.chunks));self.chunks.append({'drug':name,'section':field,'label_id':label.get('id'),'effective_time':label.get('effective_time'),'quote':excerpt})
            self.by_name[name]=indices
        self.vec=TfidfVectorizer(stop_words='english',ngram_range=(1,2),max_features=50000,min_df=2)
        self.x=self.vec.fit_transform([r['quote'] for r in self.chunks])

    def query(self,case,profile):
        q=self.vec.transform([case['dialogue']]);evidence=[];missing=[]
        weights=PROFILES[profile]
        for option in case['options']:
            name=option.strip().lower();ix=self.by_name.get(name,[])
            if not ix:missing.append(option);continue
            scores=(self.x[ix]@q.T).toarray()[:,0]
            scores*=np.array([weights.get(self.chunks[j]['section'],0) for j in ix])
            order=np.argsort(-scores,kind='stable');selected=[]
            for k in order:
                chunk=self.chunks[ix[k]]
                if not weights.get(chunk['section']) or scores[k]<=0:continue
                if any(chunk['quote'] in s['quote'] or s['quote'] in chunk['quote'] for s in selected):continue
                selected.append(chunk)
                if len(selected)==2:break
            evidence.extend(selected)
        return {'excerpts':evidence,'missing_option_labels':missing}

class EvidenceAgent(Agent):
    def __init__(self,train,model):super().__init__(train,model);self.evidence=LabelEvidence()
    def solve(self,c,state,method='cot',initial=None):
        profile=state.get('evidence_profile')
        if profile is None:return super().solve(c,state,method,initial)
        tool=self.evidence.query(c,profile)
        view=dict(c);view['dialogue']=c['dialogue']+'\nDrug-label tool excerpts (company-submitted labels via openFDA; incomplete excerpts, apply only to documented patient facts; missing text is not proof of safety):\n'+json.dumps(tool,ensure_ascii=False)
        out=super().solve(view,state,method,initial);out['label_evidence_trace']={'profile':profile,'label_ids':[x['label_id'] for x in tool['excerpts']],'missing_option_count':len(tool['missing_option_labels'])}
        return out
