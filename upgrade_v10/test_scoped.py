import unittest
from unittest.mock import patch
from run_scoped_rsi import matches,normalize_card,ScopedAgent
from agent import Agent,empty_state

class Applicability(unittest.TestCase):
    def test_whole_phrase_and_required_conditions(self):
        c={'all_terms':['renal impairment'],'any_terms':['aspirin','heparin']}
        self.assertTrue(matches(c,'Renal impairment; options include heparin.'))
        self.assertFalse(matches(c,'Renal impairment; options include another medicine.'))
        self.assertFalse(matches({'all_terms':['male'],'any_terms':[]},'female patient'))

    def test_generic_only_rules_rejected(self):
        self.assertIsNone(normalize_card({'id':'all','all_terms':['patient'],'rule':'always do this'}))

    def test_nonmatching_card_keeps_identical_actor_request(self):
        train=[{'id':str(i),'dialogue':'fictional condition medication '+str(i),'options':['x','y','z'],'gold':'A'} for i in range(3)]
        case={'id':'test','dialogue':'a fictional patient','options':['x','y','z'],'gold':'B'};requests=[]
        def fake(messages,*args,**kwargs):requests.append(messages);return {'raw':'{"final":"A"}'}
        state={'cards':[{'id':'specific','all_terms':['renal impairment'],'any_terms':[],'rule':'A conditional rule.'}]}
        with patch('agent.request',fake):
            Agent(train,'offline').solve(case,empty_state());ScopedAgent(train,'offline').solve(case,state)
        self.assertEqual(requests[0],requests[1])

if __name__=='__main__':unittest.main()
