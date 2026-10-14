import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'upgrade_v7'))
from selection_parser import compile_model_selection,bind_cached_output

class ModelEnvelope(unittest.TestCase):
    def test_empty_envelope_only(self):
        c={'O1':{'drug_name':'synthetic'}}
        r=compile_model_selection('<think>\n\n</think>\n\n{"order_ids":["O1"]}',c)
        self.assertEqual(r['orders'],[c['O1']]);self.assertEqual(r['raw_strict_status'],'invalid_json')
        self.assertTrue(r['empty_reasoning_envelope_removed'])
        r=compile_model_selection('{"order_ids":["O1"]}',c)
        self.assertFalse(r['empty_reasoning_envelope_removed']);self.assertEqual(r['status'],'valid')

    def test_nonempty_reasoning_and_malformed_payload_not_silently_repaired(self):
        c={'O1':{'drug_name':'synthetic'}}
        for text in ['<think>do something</think>{"order_ids":["O1"]}','<think></think>{"order_ids":','<think></think>{"other":["O1"]}']:
            self.assertEqual(compile_model_selection(text,c)['status'],'invalid_json')

    def test_unknown_ids_still_cannot_create_orders(self):
        c={'O1':{'drug_name':'synthetic'}}
        r=compile_model_selection('<think></think>{"order_ids":["O1","O999"]}',c)
        self.assertEqual(r['orders'],[c['O1']]);self.assertEqual(r['status'],'partial_repair')

    def test_shared_prompt_cache_rebinds_case_and_catalogue(self):
        cached={'case_id':'prior-case','raw':'{"order_ids":["O1"]}','orders':[{'drug_name':'old'}]}
        case={'case_id':'current-case','catalogue':{'O1':{'drug_name':'current'}}}
        row=bind_cached_output(cached,case)
        self.assertEqual(row['case_id'],'current-case');self.assertEqual(row['orders'],[case['catalogue']['O1']])
        self.assertEqual(cached['case_id'],'prior-case')

if __name__=='__main__':unittest.main()
