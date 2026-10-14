"""Transport-only retries retain request identity and cannot become model errors."""
import io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import public_client as c

class Transport(unittest.TestCase):
    def test_timeout_logs_metadata_and_extended_wait_preserves_cache_identity(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(c,'LOCAL',Path(folder)),patch.object(c,'BLOCK_FILE',Path(folder)/'block'),patch.object(c,'credentials',return_value='synthetic-local-test'),patch.object(c.time,'sleep'):
            payload={'choices':[{'message':{'content':'answer'},'finish_reason':'stop'}],'usage':{'cost':.001}}
            with patch.object(c.urllib.request,'urlopen',side_effect=[TimeoutError(),io.BytesIO(json.dumps(payload).encode())]) as network:
                r=c.request([],'synthetic-test',32,timeout_seconds=180)
                self.assertEqual(network.call_count,2);self.assertEqual(network.call_args.kwargs['timeout'],180)
            with patch.object(c.urllib.request,'urlopen') as network:
                cached=c.request([],'synthetic-test',32,timeout_seconds=90);network.assert_not_called()
            self.assertEqual(r['request_sha256'],cached['request_sha256'])
            failure=json.loads((Path(folder)/'transport_failures.jsonl').read_text());self.assertEqual(failure['error'],'TimeoutError')
            self.assertNotIn('synthetic-local-test',json.dumps(failure))

    def test_http_success_without_a_model_choice_is_not_a_model_output(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(c,'LOCAL',Path(folder)),patch.object(c,'BLOCK_FILE',Path(folder)/'block'),patch.object(c,'credentials',return_value='synthetic-local-test'),patch.object(c.time,'sleep'):
            with patch.object(c.urllib.request,'urlopen',side_effect=[io.BytesIO(b'{"error":{"code":502}}') for _ in range(3)]):r=c.request([],'synthetic-test',32)
            self.assertEqual(r['error'],'ProviderPayloadError');self.assertFalse(list((Path(folder)/'cache').glob('*.json')))

    def test_rate_limit_respects_retry_after(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(c,'LOCAL',Path(folder)),patch.object(c,'BLOCK_FILE',Path(folder)/'block'),patch.object(c,'credentials',return_value='synthetic-local-test'),patch.object(c.time,'sleep') as sleep:
            error=c.urllib.error.HTTPError('https://example.invalid',429,'synthetic rate limit',{'Retry-After':'45'},None)
            payload=io.BytesIO(b'{"choices":[{"message":{"content":"ok"}}]}')
            with patch.object(c.urllib.request,'urlopen',side_effect=[error,payload]):r=c.request([],'synthetic-test',32)
            self.assertEqual(r['raw'],'ok');sleep.assert_called_once_with(45.)

if __name__=='__main__':unittest.main()
