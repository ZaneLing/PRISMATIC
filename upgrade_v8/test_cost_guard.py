"""Prevent a queued evaluation from continuing to charge after its ledger cap."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import public_client as client

class CostGuard(unittest.TestCase):
    def test_incremental_external_append_and_partial_line(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(client,'LOCAL',Path(folder)):
            p=Path(folder)/'usage.jsonl';p.write_text('{"cost_usd": 1.2}\n')
            self.assertAlmostEqual(client.ledger_total(),1.2)
            with p.open('a') as f:f.write('{"cost_usd": 0.3}')
            self.assertAlmostEqual(client.ledger_total(),1.2)
            with p.open('a') as f:f.write('\n')
            self.assertAlmostEqual(client.ledger_total(),1.5)
            self.assertAlmostEqual(client.ledger_total(),1.5)

    def test_over_cap_never_contacts_provider_but_cache_remains_readable(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(client,'LOCAL',Path(folder)),patch.object(client,'BLOCK_FILE',Path(folder)/'block'),patch.dict('os.environ',{'RXRSI_PUBLIC_COST_CAP_USD':'1'}):
            (Path(folder)/'usage.jsonl').write_text('{"cost_usd": 1.1}\n')
            with patch.object(client.urllib.request,'urlopen') as network:
                with self.assertRaisesRegex(RuntimeError,'before request'):client.request([],'test-model',32)
                network.assert_not_called()
            body={'model':'test-model','messages':[],'temperature':0,'max_tokens':32,'provider':{'zdr':True,'data_collection':'deny'}}
            cache=Path(folder)/'cache'/(client.digest(body)+'.json');cache.write_text(json.dumps({'raw':'cached'}))
            self.assertEqual(client.request([],'test-model',32)['raw'],'cached')

if __name__=='__main__':unittest.main()
