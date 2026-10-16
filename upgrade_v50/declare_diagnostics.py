"""Declare corrected-interface diagnostics after state freeze, before test scoring."""
from common import *
import json,time
import component_ablation,catalogue_permutation
def main():
    assert not (HERE/'results/comparison.json').exists()
    component_ablation.declare();catalogue_permutation.declare()
    for name in ['component_protocol.json','permutation_protocol.json']:
        p=HERE/name;d=json.loads(p.read_text());d.update(corrected_interface=True,
          prior_literal_schema_test_scores_observed=True,
          fresh_per_batch_generation=True,unchanged_effective_states_reuse_predictions=True)
        save(p,d)
    print('Corrected-interface diagnostics fixed before corrected test scoring')
if __name__=='__main__':main()
