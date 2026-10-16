"""Run pinned author memory core with a local LLM and semantic embeddings.

This is NOT the authors' full ReAct/web-tool benchmark. Actor, tools, task,
embedding backend, reward and training budget are explicitly adapted.
"""
import json,sys,collections
from dataclasses import asdict
from types import SimpleNamespace
from common import *
sys.path.insert(0,str(RESOURCES/'SkeMex/src'))
from medmem_agent.evolution.config import EvoConfig
from medmem_agent.evolution.storage import SkillStore
from medmem_agent.evolution.encode import TrajectoryEncoder
from medmem_agent.evolution.governance import SkillGovernance
from medmem_agent.evolution.utility import UtilityUpdater
from medmem_agent.evolution.retrieve import SkillRetriever
from medmem_agent.evolution.types import Trajectory,EncodeResult
import medmem_agent.evolution.governance as governance_module
from local_backend import Backend
from actor import run
from local_embeddings import LocalEmbeddings

class NeedBatch(Exception):pass
class LocalCalls:
    def __init__(self,b):self.b=b;self.responses={};self.pending={};self.defer=True
    def llm(self,cap):
        parent=self
        class LLM:
            def generate(self,*,system_prompt,user_prompt,**kw):
                msg=[{'role':'system','content':system_prompt},{'role':'user','content':user_prompt}]
                sig=digest([msg,cap])
                if sig not in parent.responses:
                    if parent.defer:parent.pending[sig]=(msg,cap);raise NeedBatch()
                    parent.responses[sig]=parent.b.batch([msg],cap,'skemex/govern')[0]['raw']
                return SimpleNamespace(content=parent.responses[sig])
        return LLM()
    def flush(self):
        pending=self.pending;self.pending={}
        for cap in sorted({x[1] for x in pending.values()}):
            chunk=[(k,v[0]) for k,v in pending.items() if v[1]==cap]
            recs=self.b.batch([v for k,v in chunk],cap,'skemex/encode')
            for (k,v),r in zip(chunk,recs):self.responses[k]=r['raw']
def main():
    b=Backend('qwen');data=load_cases();data['train']+=json.loads((PRIVATE/'training-stream-2.json').read_text());cfg=EvoConfig()
    cfg.storage.experiment_root='skemex-store';cfg.storage.root_dir='skemex-cache'
    cfg.retrieval.pre_screen.enabled=False
    cfg.context_guard.context_trim_observation_chars=12000
    store=SkillStore(str(PRIVATE),cfg);store.ensure_initialized()
    calls=LocalCalls(b)
    TrajectoryEncoder._build_llm=lambda self,model,max_tokens:calls.llm(max_tokens)
    governance_module.build_llm=lambda config:calls.llm(config.max_tokens)
    embeddings=LocalEmbeddings();embeddings.precompute([c['input'] for c in data['train']+data['test']]);retriever=SkillRetriever(store,embeddings,cfg)
    encoder=TrajectoryEncoder(store,cfg);governance=SkillGovernance(store,embeddings,cfg);updater=UtilityUpdater(store,cfg)
    rounds=[]
    def inject(cases,r):
        out=[]
        for c in cases:
            ret=retriever.retrieve(c['input'],['prescribing'],r,['offline_label','order_catalogue'])
            out.append({**c,'retrieved_memory':ret.retrieved_skills_block,'injected_ids':ret.injected_skill_ids})
        return out
    for r in range(1,7):
        cases=inject(data['train'][(r-1)*24:r*24],r);rows=run(b,cases,'skemex',tag=f'skemex/train-{r}')
        save(PRIVATE/f'skemex-train-{r}.json',rows)
        trajectories=[]
        for c,row in zip(cases,rows):
            reward=score([row['orders']],[c['gold']])['promotion_score']
            trajectories.append(Trajectory(id=c['case_id'],dataset='mimic_order',query=c['input'],task_category=['prescribing'],
              steps=[{'action':'observe_patient','observation':c['input']},
                     {'action':'order_catalogue','action_input':c['catalogue'],'observation':json.dumps(row['evidence'])},
                     {'action':'assess','observation':row['assessment'],'answer':json.dumps(row['orders'])}],
              injected_skill_ids=c['injected_ids'],prediction=row['raw'],ground_truth=c['gold'],eval_result=reward))
        results={};adapter_errors=[]
        while len(results)<len(trajectories):
            for t in trajectories:
                if t.id in results:continue
                try:results[t.id]=encoder.encode(t,'offline_label: frozen product labels; order_catalogue: joint training templates')
                except NeedBatch:pass
                except (TypeError,ValueError,AttributeError,KeyError) as e:
                    adapter_errors.append({'stage':'encode','type':type(e).__name__})
                    results[t.id]=EncodeResult(trajectory_id=t.id,output_action='NONE')
            if calls.pending:calls.flush()
            elif len(results)<len(trajectories):raise RuntimeError('Encoder made no progress')
        calls.defer=False
        created=[]
        for result in results.values():
            try:s=governance.apply_encode_result(result)
            except (TypeError,ValueError,AttributeError,KeyError) as e:
                adapter_errors.append({'stage':'materialize','type':type(e).__name__});s=None
            if s:created.append(s.id)
        updater.update_window(trajectories,results,current_window=r)
        managed=governance.manage();calls.defer=True
        save(PRIVATE/f'skemex-encode-{r}.json',{k:asdict(v) for k,v in results.items()})
        rounds.append({'round':r,'cases_seen':r*24,'created':len(created),'active':sum(s.branch!='meta_memory' for s in store.list_skills(statuses=['active','mature'])),
          'actions':dict(collections.Counter(x.output_action for x in results.values())),'governance_counts':{k:len(v) for k,v in managed.items()}})
        rounds[-1]['adapter_errors']=adapter_errors
        save(HERE/'results/skemex_learning.json',{'rounds':rounds,'complete':False})
    store.read_only=True
    cases=inject(data['test'],6)
    save(HERE/'skemex_freeze.json',{'source_commit':'a640474590e384669dd71b657c441264beef73d2',
      'skill_state_sha256':digest([s.to_dict() for s in store.list_skills()]),'test_labels_used':False,
      'adaptations':['common three-call prescription actor','offline MiniLM semantic embeddings with full-text chunk pooling','continuous order-agreement reward','144 training cases','no web tools','pre-screening disabled; all active skills enter scoring']})
    rows=run(b,cases,'skemex',tag='skemex/test');save(PRIVATE/'qwen-test-skemex.json',{'rows':rows})
    save(HERE/'results/skemex.json',{'method':'SkeMex author memory core + common actor','metrics':metrics(rows,cases),'complete':True})
    save(HERE/'results/skemex_learning.json',{'rounds':rounds,'complete':True})
if __name__=='__main__':main()
