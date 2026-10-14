"""Verify the feedback/compute claims before expensive patient-data fitting."""
import unittest
import numpy as np
from scipy.sparse import csr_matrix
from components import WeightedPolicy,feedback_weights,drug_mask

class Contracts(unittest.TestCase):
    def test_empty_reachable_target_and_exact_prediction_receive_no_error_weight(self):
        p=np.array([[.9,.1],[.1,.1],[.9,.1]])
        y=np.array([[1,0],[0,0],[0,1]])
        self.assertTrue(np.array_equal(feedback_weights(p,y,.5),[1,1,4]))

    def test_twenty_order_limit_and_permutation_preserve_weight_distribution(self):
        p=np.linspace(0,1,62).reshape(2,31);y=(p>.9).astype(int)
        self.assertTrue((drug_mask(p,.1).sum(1)<=20).all())
        w=feedback_weights(p,y,.1);permuted=w[::-1]
        self.assertTrue(np.array_equal(np.sort(w/w.mean()),np.sort(permuted/permuted.mean())))

    def test_all_classifiers_receive_exact_epoch_budget(self):
        x=np.random.default_rng(42).normal(size=(80,5));y=np.column_stack([x[:,0]>0,x[:,1]>0]).astype(float)
        model=WeightedPolicy(csr_matrix(x),y,np.ones(80),42,epochs=4)
        self.assertEqual(model.iterations,[4,4]);self.assertEqual(model.predict_proba(csr_matrix(x)).shape,(80,2))

if __name__=='__main__':unittest.main()
