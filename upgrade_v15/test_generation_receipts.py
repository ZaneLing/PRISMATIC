"""Regression for duplicate prompts with different case/catalogue identities."""
import json,tempfile,unittest
from pathlib import Path
from generation_receipts import infer_with_receipts

class ReceiptContracts(unittest.TestCase):
    def test_duplicate_prompts_generate_once_and_bind_every_case(self):
        with tempfile.TemporaryDirectory() as folder:
            cases=[{'case_id':'a','messages':[{'role':'user','content':'identical prompt'}],'catalogue':{'O1':'order-a'}},
                   {'case_id':'b','messages':[{'role':'user','content':'identical prompt'}],'catalogue':{'O1':'order-b'}}]
            calls=[]
            def generate(rows):calls.extend(rows);return [{'raw':'select O1'} for c in rows]
            def bind(row,c):return {**row,'case_id':c['case_id'],'orders':[c['catalogue']['O1']]}
            a=infer_with_receipts(cases,'model',folder,generate,bind)
            self.assertEqual(len(calls),1);self.assertEqual([r['orders'] for r in a],[['order-a'],['order-b']])
            self.assertNotEqual(a[0]['case_receipt_key'],a[1]['case_receipt_key'])
            b=infer_with_receipts(cases,'model',folder,generate,bind);self.assertEqual(a,b);self.assertEqual(len(calls),1)
            p=Path(folder)/'cases'/(a[0]['case_receipt_key']+'.json');x=json.loads(p.read_text());x['raw']='corrupted';p.write_text(json.dumps(x))
            with self.assertRaisesRegex(AssertionError,'Immutable case receipt mismatch'):infer_with_receipts(cases,'model',folder,generate,bind)

if __name__=='__main__':unittest.main()
