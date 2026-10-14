"""Download the public author-linked graph resource, enforcing the observed hash.

Source: SafeDrug README's drug-DDI.csv link. This is research graph data, not a
clinical prescribing knowledge base. Downloads remain outside the repository.
"""
from pathlib import Path
from html.parser import HTMLParser
import hashlib,json,urllib.request,urllib.parse

URL='https://drive.google.com/uc?export=download&id=1mnPc0O0ztz0fkv3HF-dpmBb8PLWsEoDz'
EXPECTED='60bd3d071345473236f56638ebb732c3c964f0fd3468fdd29a444bcc1bf80d35'

class Form(HTMLParser):
    def __init__(self):super().__init__();self.action=None;self.fields={}
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='form':self.action=a.get('action')
        if tag=='input' and a.get('name'):self.fields[a['name']]=a.get('value','')

def download():
    out=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources/drug-DDI.csv'
    out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists() and hashlib.sha256(out.read_bytes()).hexdigest()==EXPECTED:return out
    response=urllib.request.urlopen(URL,timeout=30)
    if 'html' in response.headers.get('content-type',''):
        parser=Form();parser.feed(response.read().decode());response.close()
        if urllib.parse.urlparse(parser.action or '').hostname!='drive.usercontent.google.com':
            raise ValueError('Unexpected download form; inspect the public source')
        response=urllib.request.urlopen(parser.action+'?'+urllib.parse.urlencode(parser.fields),timeout=30)
    if 'html' in response.headers.get('content-type',''):raise ValueError('Resource not returned')
    temp=out.with_suffix('.download');digest=hashlib.sha256();n=0
    try:
        with response,temp.open('wb') as f:
            while True:
                b=response.read(1024*1024)
                if not b:break
                n+=len(b)
                if n>512*1024*1024:raise ValueError('Resource exceeds 512 MiB cap')
                f.write(b);digest.update(b)
        if digest.hexdigest()!=EXPECTED:raise ValueError('Resource version differs from pinned hash')
        temp.replace(out)
    finally:
        if temp.exists():temp.unlink()
    return out

if __name__=='__main__':print(json.dumps({'path':str(download()),'sha256':EXPECTED}))
