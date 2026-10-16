"""No cloud embeddings: a persistent subprocess on the same local computer."""
import subprocess,json,atexit
from common import *
class LocalEmbeddings:
    def __init__(self):
        self.path=PRIVATE/'semantic_embeddings.json';self.cache=json.loads(self.path.read_text()) if self.path.exists() else {}
        python=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.venv/bin/python'
        self.log=(PRIVATE/'embedding-worker.log').open('a')
        self.worker=subprocess.Popen([str(python),str(HERE/'embedding_worker.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,text=True,bufsize=1)
        atexit.register(self.close)
    def precompute(self,texts):
        missing=list(dict.fromkeys(t for t in texts if digest(t) not in self.cache))
        for lo in range(0,len(missing),64):
            chunk=missing[lo:lo+64];self.worker.stdin.write(json.dumps({'texts':chunk})+'\n');self.worker.stdin.flush()
            response=self.worker.stdout.readline()
            if not response:raise RuntimeError('Local embedding worker exited; see restricted log')
            d=json.loads(response)
            if 'error' in d:raise RuntimeError(d['error'])
            assert len(d['vectors'])==len(chunk)
            for text,v in zip(chunk,d['vectors']):assert len(v)==384;self.cache[digest(text)]=v
            save(self.path,self.cache)
    def similarity(self,a,b):
        self.precompute([a,b]);return max(0,min(1,sum(x*y for x,y in zip(self.cache[digest(a)],self.cache[digest(b)]))))
    def close(self):
        if self.worker.poll() is None:self.worker.stdin.close();self.worker.terminate()
        self.log.close()
