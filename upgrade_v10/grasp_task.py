"""Public option-selection Task adapter for the unmodified GRASP core."""
import json,threading
from collections import defaultdict
from grasp import Task,Rollout
from public_client import LOCAL,request,json_object,digest
from agent import BASE,COT,MODULES

class PublicBackend:
    def __init__(self,model,temperature=0):
        self.model=model;self.temperature=temperature;self.calls=defaultdict(int);self.lock=threading.Lock()

    def inference(self,history,tools=None):
        assert tools is None,'This adapter is for the option-selection task.'
        messages=[{'role':'assistant' if m['role']=='agent' else m['role'],'content':m['content']} for m in history]
        # The released core constructs its separate proposer with temperature 0.7.
        proposer=self.temperature>0
        salt=None
        if proposer:
            key=digest(messages)
            with self.lock:index=self.calls[key];self.calls[key]+=1
            salt=['grasp-official-core',key,index]
        return request(messages,self.model,3072 if proposer else 512,'grasp_proposer' if proposer else 'grasp_actor',
            temperature=self.temperature,cache_salt=salt)['raw']

class MedicationTask(Task):
    name='rxsafebench-derived-option-selection'
    updater_task_family='public fictional medication option selection'
    updater_guidance='Use training ground-truth feedback to learn conditional decision procedures. Do not memorize letters, case IDs, question templates or undocumented patient facts. This is a single-step choice task; no external API actions are available.'
    updater_failure_examples='indication_mismatch, missed_explicit_contraindication, missed_current_medication_interaction, invalid_final_json'

    def __init__(self):
        data=json.loads((LOCAL/'data.json').read_text());p=data['parts']
        # Same total development labels as v8; the original core uses its own
        # balanced training probes and a separate best-checkpoint validation set.
        self.parts={'dev':p['train'],'val':p['proposal']+p['guard'],'test':p['test']}
        self.transfer=data['transfer']

    def samples(self,split):
        return [dict(c,description=c['dialogue'],answer=c['gold']) for c in self.parts[split]]

    def rollout(self,sample,agent):
        prompt=BASE+'\n'+COT+'\n'+'\n'.join(MODULES.values())+'\nCurrent question:\n'+sample['dialogue']
        prompt+='\nOptions:\n'+'\n'.join(f'{chr(65+i)}. {o}' for i,o in enumerate(sample['options']))
        prompt+='\nReturn JSON only: {"evidence":"short decisive evidence","final":"one option letter"}.'
        history=[{'role':'system','content':'Solve a verified public, fictional medication benchmark.'},{'role':'user','content':prompt}]
        raw=agent.inference(history);parsed=json_object(raw);answer=parsed.get('final') if isinstance(parsed,dict) else None
        if isinstance(answer,str):answer=answer.strip().upper()
        if answer not in [chr(65+i) for i in range(len(sample['options']))]:answer=None
        return Rollout(history=history+[{'role':'assistant','content':raw}],agent_actions=[raw],answer=answer or '',
            status='completed' if answer else 'agent invalid action',raw={'reported_answer':answer,'evidence':parsed.get('evidence','') if isinstance(parsed,dict) else ''})

    def evaluate(self,sample,rollout):return rollout.answer==sample['gold']
    def failure_tags(self,sample,rollout):return ['invalid_final_json'] if not rollout.answer else ['wrong_'+sample['type']+'_selection']
