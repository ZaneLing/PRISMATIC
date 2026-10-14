import copy,unittest
import numpy as np
from verifier import features,select_rows

class LeakageContracts(unittest.TestCase):
    def test_features_do_not_read_ground_truth(self):
        case={'dialogue':'A public synthetic question.','options':['drug one','drug two','drug three'],'gold':'A'}
        b={'case_id':'x','prediction':'A','evidence':'drug one is recommended'}
        r={'case_id':'x','prediction':'B','evidence':'avoid drug one; drug two is appropriate'}
        x=features([case],[b],[r]);changed=copy.deepcopy(case);changed['gold']='C'
        self.assertEqual((x-features([changed],[b],[r])).nnz,0)
    def test_case_alignment_is_required(self):
        with self.assertRaises(AssertionError):select_rows([{'case_id':'a'}],[{'case_id':'b'}],[1])
    def test_invalid_reply_and_full_cost_are_retained(self):
        c={'dialogue':'Question','options':['one','two','three']}
        b={'case_id':'x','prediction':None,'cost_usd':1}
        r={'case_id':'x','prediction':'B','cost_usd':3}
        self.assertTrue(np.isfinite(features([c],[b],[r]).data).all())
        self.assertEqual(select_rows([b],[r],[0])[0]['cost_usd'],3)

if __name__=='__main__':unittest.main()
