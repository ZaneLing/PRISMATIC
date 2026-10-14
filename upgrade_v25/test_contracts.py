"""Synthetic checks for distinct native-code fields, empty feedback and unseen labels."""
import unittest
import numpy as np
from scipy.sparse import csr_matrix
from data_contract import order
from learning import score,feedback_weights,Policy,OrderTool,ranked_rows,choose

class Contracts(unittest.TestCase):
    def test_native_fields_preserved(self):
        o=order({'hicl':123,'routeadmin':' PO ','dosage':' 2  tablets ','frequency':' Every 6 Hours '})
        self.assertEqual(o,{'drug_code':'hicl:123','route':'po','dosage':'2 tablets','frequency':'every 6 hours'})
        self.assertNotIn('dose_unit',o)
    def test_unknown_gold_code_remains_in_recall(self):
        a={'drug_code':'hicl:1','route':'po','dosage':'1 mg','frequency':'daily'}
        b=dict(a,drug_code='hicl:2');m=score([[a]],[ [a,b] ])
        self.assertEqual(m['drug_recall'],.5);self.assertAlmostEqual(m['drug_micro_f1'],2/3)
    def test_empty_feedback_not_a_failure(self):
        p=np.array([[.01,.02],[.8,.01]]);gold=np.array([[0,0],[0,0]])
        np.testing.assert_array_equal(feedback_weights(p,gold,.5),[1,4])
    def test_missing_attributes_not_invented(self):
        o=order({'hicl':123,'routeadmin':'po','dosage':None,'frequency':'daily'})
        m=score([[o]],[[o]]);self.assertEqual(m['drug_micro_f1'],1);self.assertEqual(m['complete_gold_orders'],0);self.assertEqual(m['predicted_order_completion'],0)
    def test_float32_policy_and_conditional_order_integration(self):
        x=csr_matrix(np.array([[1,i%5,i%2] for i in range(100)],dtype=np.float32))
        y=np.array([[i%5!=0,i%5!=1] for i in range(100)],dtype=float);weights=np.linspace(1,2,100)
        model=Policy(x,y,weights,42);self.assertEqual(model.iterations,[60,60])
        truth=[[{'drug_code':'hicl:'+str(j+1),'route':'po','dosage':str(1+i%2)+' mg','frequency':'daily'} for j in range(2) if y[i,j]] for i in range(100)]
        tool=OrderTool(truth,x,42);self.assertEqual(len(tool.models),2)
        rows,p=ranked_rows(model.predict_proba(x[:3]),tool,x[:3],['hicl:1','hicl:2'])
        predicted=choose(rows,p,0);self.assertEqual([len(r) for r in predicted],[2,2,2])
        self.assertTrue(all(o in truth[1]+truth[2]+truth[3]+truth[4] for row in predicted for o in row))

if __name__=='__main__':unittest.main()
