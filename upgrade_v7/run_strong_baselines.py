"""Broader same-data controls; select configurations on proposal validation only."""
import json,time,sys
from pathlib import Path
import joblib,numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.multiclass import OneVsRestClassifier
from sklearn.naive_bayes import MultinomialNB
from prepare_data import PRIVATE
from rx_agent import score
from run_rounds import choose
HERE=Path(__file__).resolve().parent

def run(seed):
    begin=time.time();b=joblib.load(PRIVATE/'data.joblib');run=joblib.load(PRIVATE/f'run_seed_{seed}.joblib')
    classes=b['classes'];truth=b['truth'];y=np.array([[c in {o['drug_name'] for o in row} for c in classes] for row in truth['train']],dtype=np.float32)
    tool=run['tools'][40000];x=run['x'];cache={};models={};config={'alphas':[1e-6,1e-5,1e-4],'weights':[0,.25,.5,.75,1],'thresholds':[.1,.15,.2,.25,.3,.4,.5]}
    (HERE/'results/strong_baseline_protocol.json').write_text(json.dumps(config,indent=2)+'\n')
    char=TfidfVectorizer(min_df=3,max_features=24000,analyzer='char_wb',ngram_range=(3,5),sublinear_tf=True)
    char.fit(b['text']['train'][:8000]);cx={s:char.transform(t) for s,t in b['text'].items()}
    all_predictions={};validation={};selection={}
    def evaluate(p,split,threshold,conditional):
        rank=np.argsort(-p,axis=1,kind='stable')[:,:20]
        names=[[classes[j] for j in row if p[i,j]>=(threshold[j] if isinstance(threshold,np.ndarray) else threshold)] for i,row in enumerate(rank)]
        return tool.compile(names,x[split],conditional)
    families={}
    for view,mat in [('word',x),('char',cx)]:
        for alpha in config['alphas']:
            name=f'{view}-{alpha}';clf=OneVsRestClassifier(SGDClassifier(loss='log_loss',alpha=alpha,max_iter=60,tol=1e-3,random_state=seed),n_jobs=1)
            clf.fit(mat['train'],y);models[name]=(clf,mat)
            pv=clf.predict_proba(mat['proposal']);cache[name]=pv;best=None
            for conditional in [False,True]:
                for t in config['thresholds']:
                    m=score(evaluate(pv,'proposal',t,conditional),truth['proposal']);choice=(m['promotion_score'],name,t,conditional)
                    if best is None or choice[0]>best[0]:best=choice
            validation[name]=best
        families[view]=max((v for k,v in validation.items() if k.startswith(view+'-')),key=lambda z:z[0])
        print(json.dumps({'seed':seed,'family':view,'selection':families[view]}),flush=True)
    wp=cache[families['word'][1]];cp=cache[families['char'][1]];best=None
    for w in config['weights']:
        pv=w*wp+(1-w)*cp
        for conditional in [False,True]:
            for t in config['thresholds']:
                m=score(evaluate(pv,'proposal',t,conditional),truth['proposal']);choice=(m['promotion_score'],w,t,conditional)
                if best is None or choice[0]>best[0]:best=choice
    families['word_char_ensemble']=best
    nb=OneVsRestClassifier(MultinomialNB(alpha=1),n_jobs=1);nb.fit(x['train'],y);npv=nb.predict_proba(x['proposal']);best=None
    for conditional in [False,True]:
        for t in config['thresholds']:
            val=score(evaluate(npv,'proposal',t,conditional),truth['proposal']);choice=(val['promotion_score'],'NB',t,conditional)
            if best is None or choice[0]>best[0]:best=choice
    families['multinomial_nb']=best
    # Freeze before this baseline runner reads test targets for scoring.
    (HERE/f'results/strong_selection_seed_{seed}.json').write_text(json.dumps({'families':families,'all_validation':validation},indent=2)+'\n')
    test_prob={view:models[families[view][1]][0].predict_proba(models[families[view][1]][1]['test']) for view in ['word','char']}
    w=families['word_char_ensemble'][1];test_prob['word_char_ensemble']=w*test_prob['word']+(1-w)*test_prob['char'];test_prob['multinomial_nb']=nb.predict_proba(x['test'])
    for family,choice in families.items():all_predictions[family]=evaluate(test_prob[family],'test',choice[2],choice[3])
    report={'seed':seed,'method_scores':{n:score(p,truth['test']) for n,p in all_predictions.items()},'seconds':time.time()-begin}
    joblib.dump({'predictions':all_predictions,'models':models,'char_vectorizer':char,'families':families},PRIVATE/f'strong_seed_{seed}.joblib')
    (HERE/f'results/strong_results_seed_{seed}.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

if __name__=='__main__':run(int(sys.argv[1]) if len(sys.argv)>1 else 42)
