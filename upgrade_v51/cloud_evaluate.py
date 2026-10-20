"""Post-freeze controls, cross-model transfer and paired uncertainty."""
import json
import common
common.PRIVATE=common.PRIVATE/"cloud"
from common import *
from local_backend import Backend
from learn import execute,evaluated
from policy import PROCEDURES
from audit_results import paired

def main():
 data=load_cases();cs=data['audit'];learning=json.loads((PRIVATE/'learning.json').read_text());assert learning['complete'];freeze=json.loads((PRIVATE/'freeze.json').read_text());assert not freeze['selection_used_audit']
 initial={'cards':[]};final=learning['state'];ops=json.loads((HERE/'followup_protocol.json').read_text())['frozen_static_control']
 static={'cards':[{'root_cause':'Researcher fixed control','cluster':'manual_bundle','when':'all','unless':[],'operator':op,'instruction':'Apply the listed procedure only to observed inputs.','counterexample':'Missing observations do not establish an indication.'} for op in ops]}
 b=Backend();base=execute(b,cs,initial,'audit-round-0');selected=execute(b,cs,final,'audit-final');control=execute(b,cs,static,'audit-static-repairs')
 draft={'cards':[c for c in static['cards'] if c['operator']=='ranked_draft']}
 draftrows=execute(b,cs,draft,'audit-static-ranked-draft')
 top8=[{'case_id':c['case_id'],'orders':[o for o in c['catalogue'].values() if o['drug_name'] in c['retrieval_meta']['classifier_rank'][:8]],'catalogue':c['catalogue'],'invalid':False} for c in cs]
 results={'qwen':{'initial':evaluated(base,cs),'selected':evaluated(selected,cs),'static_repairs':evaluated(control,cs),'static_ranked_draft':evaluated(draftrows,cs),'frozen_top8':evaluated(top8,cs),'ranked_draft_to_selected':paired(cs,draftrows,selected),'initial_to_selected':paired(cs,base,selected),'static_to_selected':paired(cs,control,selected)}}
 del b
 import gc;gc.collect()
 import mlx.core as mx;mx.clear_cache()
 b=Backend('llama');a=execute(b,cs,initial,'llama-audit-initial');z=execute(b,cs,final,'llama-audit-selected') if final!=initial else a
 results['llama']={'initial':evaluated(a,cs),'selected':evaluated(z,cs),'initial_to_selected':paired(cs,a,z)}
 save(HERE/'results/cloud/controls_transfer.json',{'complete':True,'methods':results,'cases':len(cs),'api_cost_usd':0,'selection_used_audit':False,'transfer_finetuning':False,'static_control_is_manual':True})
if __name__=='__main__':main()
