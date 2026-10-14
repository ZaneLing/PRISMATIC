import json,unittest
from selection_parser import compile_model_selection,bind_cached_output

class MaskContracts(unittest.TestCase):
    def setUp(self):self.c={f'O{i}':{'drug_name':str(i)} for i in range(1,21)}
    def test_explicit_exclusion_and_order(self):
        x=compile_model_selection(json.dumps({'include':[0,1]+[0]*18}),self.c)
        self.assertEqual(x['orders'],[self.c['O2']])
    def test_partial_and_bool_masks_rejected(self):
        for mask in [[0]*19,[False]*20,[2]*20]:
            self.assertEqual(compile_model_selection(json.dumps({'include':mask}),self.c)['status'],'invalid_json')
    def test_only_empty_envelope_allowed_and_cache_rebound(self):
        raw='<think>\n</think>\n'+json.dumps({'include':[0]*20})
        x=bind_cached_output({'case_id':'old','raw':raw},{'case_id':'new','catalogue':self.c})
        self.assertEqual(x['case_id'],'new');self.assertEqual(x['status'],'valid')
        self.assertEqual(compile_model_selection(raw.replace('\n</think>','Reason</think>'),self.c)['status'],'invalid_json')

if __name__=='__main__':unittest.main()
