"""Offline contracts for information flow, parsing and regression counts."""
import copy,json,unittest
from unittest.mock import patch
from agent import Agent,empty_state,transition,normalize_state

class Contracts(unittest.TestCase):
    def setUp(self):
        self.train=[{'id':'train-'+str(i),'dialogue':'Fictional patient condition and medication '+str(i),'options':['alpha','beta','gamma'],'gold':'A','type':'synthetic'} for i in range(3)]
        self.agent=Agent(self.train,'offline-test')
        self.case={'id':'heldout','dialogue':'Fictional patient has a condition. Current medication is alpha.','options':['alpha','beta','gamma'],'gold':'B','type':'synthetic'}

    def test_current_gold_cannot_change_actor_prompt(self):
        prompts=[]
        def fake(messages,*a,**kw):prompts.append(messages);return {'raw':'{"evidence":"test","final":"B"}'}
        with patch('agent.request',fake):
            self.agent.solve(self.case,empty_state())
            changed=copy.deepcopy(self.case);changed['gold']='C';self.agent.solve(changed,empty_state())
        self.assertEqual(prompts[0],prompts[1])

    def test_memory_is_training_only_and_excludes_current(self):
        state=empty_state();state['memory_ids']=['heldout','unknown']+[x['id'] for x in self.train]
        matches=self.agent.retrieve(self.train[0],state)
        self.assertTrue(matches)
        self.assertNotIn('train-0',[x['case_id'] for x in matches])
        self.assertTrue(all(x['case_id'] in self.agent.by_id for x in matches))

    def test_focus_returns_exact_patient_text(self):
        state=empty_state();state['focus_terms']=['medication']
        self.assertTrue(all(x in self.case['dialogue'] for x in self.agent.focus(self.case,state)))

    def test_parser_does_not_use_letter_in_evidence(self):
        with patch('agent.request',return_value={'raw':'{"evidence":"A seems attractive but contraindicated","final":"C"}'}):
            self.assertEqual(self.agent.solve(self.case,empty_state())['prediction'],'C')
        with patch('agent.request',return_value={'raw':'A occurs in an invalid response'}):
            self.assertIsNone(self.agent.solve(self.case,empty_state())['prediction'])

    def test_transition_counts_repair_and_regression_separately(self):
        cases=[{'gold':'A'},{'gold':'B'},{'gold':'C'}]
        before=[{'prediction':x} for x in ['B','B','C']];after=[{'prediction':x} for x in ['A','A','C']]
        self.assertEqual(transition(before,after,cases),{'fixes':1,'regressions':1,'retained_correct':1})

    def test_bounded_state(self):
        state=empty_state();state['skills']=[{'id':str(i),'text':'x'*1000} for i in range(10)]
        state=normalize_state(state);self.assertEqual(len(state['skills']),6);self.assertEqual(len(state['skills'][0]['text']),900)

if __name__=='__main__':unittest.main()
