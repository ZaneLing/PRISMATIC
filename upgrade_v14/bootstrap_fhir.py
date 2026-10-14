"""Extract the official MedAgentBench Java app/data for an isolated native runtime.

No Docker daemon or system-wide Java installation is required. Image layers and
JRE archives are checksum-verified. Only regular files/directories under explicit
prefixes are extracted, without executing image setup commands.
"""
import hashlib,json,shutil,tarfile,time,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
LOCAL=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/medagentbench-native'
REPO='jyxsu6/medagentbench'
MANIFEST='sha256:3fb83d7ed71c5476f9eb6212bd440a909ef7505922bbc757dc488a8fc0701966'

def read_json(url,headers=None):
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers or {}),timeout=60) as r:return json.load(r)

def registry_headers():
    d=read_json('https://auth.docker.io/token?service=registry.docker.io&scope=repository:'+REPO+':pull')
    return {'Authorization':'Bearer '+d['token'],'Accept':'application/vnd.docker.distribution.manifest.v2+json'}

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def download(url,path,expected,headers=None):
    if path.exists() and sha(path)==expected:return
    tmp=path.with_suffix('.part');last=time.time()
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=headers or {}),timeout=60) as response,tmp.open('wb') as out:
                total=0
                while True:
                    block=response.read(4*1024*1024)
                    if not block:break
                    out.write(block);total+=len(block)
                    if time.time()-last>20:
                        print(json.dumps({'download':path.name,'megabytes':round(total/1e6,1)}),flush=True);last=time.time()
            assert sha(tmp)==expected,'Artifact checksum mismatch'
            tmp.replace(path);return
        except Exception:
            if attempt==2:raise
            time.sleep(2)

def extract_regular(archive,destination,prefixes):
    selected=[];destination.mkdir(parents=True,exist_ok=True)
    with tarfile.open(archive) as tar:
        for member in tar:
            name=member.name.lstrip('./')
            if not any(name==p.rstrip('/') or name.startswith(p) for p in prefixes):continue
            assert '..' not in Path(name).parts and not Path(name).is_absolute()
            target=destination/name
            assert target.resolve().is_relative_to(destination.resolve()) if hasattr(Path,'is_relative_to') else str(target.resolve()).startswith(str(destination.resolve())+'/')
            if member.isdir():target.mkdir(parents=True,exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True,exist_ok=True)
                with tar.extractfile(member) as src,target.open('wb') as out:shutil.copyfileobj(src,out)
                target.chmod(member.mode&0o777);selected.append({'path':name,'size':member.size})
    return selected

def main():
    LOCAL.mkdir(exist_ok=True);cache=LOCAL/'downloads';cache.mkdir(exist_ok=True);(HERE/'results').mkdir(exist_ok=True)
    m=read_json('https://registry-1.docker.io/v2/'+REPO+'/manifests/'+MANIFEST,registry_headers())
    selected=[]
    # Verified published image history: app, configuration, dataset. Linux/JRE
    # base layers and optional telemetry agent are intentionally not executed.
    for i in [34,36,37]:
        layer=m['layers'][i];h=layer['digest'].split(':')[1];path=cache/(h+'.tar.gz')
        download('https://registry-1.docker.io/v2/'+REPO+'/blobs/'+layer['digest'],path,h,registry_headers())
        marker=cache/(h+'.extracted.json')
        if marker.exists():files=json.loads(marker.read_text())
        else:
            files=extract_regular(path,LOCAL/'runtime',['app/','configs/','data/']);marker.write_text(json.dumps(files))
        selected.append({'index':i,'digest':layer['digest'],'compressed_bytes':layer['size'],'files':files})
        print(json.dumps({'layer_extracted':i,'files':len(files)}),flush=True)
    # The initial Temurin API request was unavailable (HTTP 403). Use Amazon's
    # documented public archive and checksum endpoints, pinned after resolution.
    metadata=cache/'java-artifact.json'
    if metadata.exists():package=json.loads(metadata.read_text())
    else:
        name='amazon-corretto-21-aarch64-macos-jdk.tar.gz'
        with urllib.request.urlopen('https://corretto.aws/downloads/latest_sha256/'+name,timeout=60) as r:checksum=r.read().decode().strip().split()[0]
        assert len(checksum)==64 and all(c in '0123456789abcdef' for c in checksum)
        with urllib.request.urlopen(urllib.request.Request('https://corretto.aws/downloads/latest/'+name,method='HEAD'),timeout=60) as r:link=r.url
        package={'link':link,'checksum':checksum,'version':link.split('/resources/')[1].split('/')[0]}
        metadata.write_text(json.dumps(package,indent=2)+'\n')
    archive=cache/'corretto21-macos-aarch64.tar.gz';download(package['link'],archive,package['checksum'])
    marker=cache/'java.extracted.json'
    if not marker.exists():
        with tarfile.open(archive) as tar:prefix=tar.next().name.split('/')[0]+'/'
        files=extract_regular(archive,LOCAL/'java',[prefix]);marker.write_text(json.dumps(files))
    java=list((LOCAL/'java').glob('*/Contents/Home/bin/java'))
    assert len(java)==1
    report={'status':'downloaded_and_verified','official_repository':'https://github.com/stanfordmlgroup/MedAgentBench',
        'image_repository':REPO,'image_manifest_digest':MANIFEST,'selected_layers':selected,
        'jre':{'vendor':'Amazon Corretto','version':package['version'],'sha256':package['checksum'],'source':package['link']},
        'runtime_difference':'Official app and public database extracted unchanged; native macOS aarch64 JRE replaces Linux amd64 container runtime. Equivalence still requires live capability and benchmark validation.',
        'system_installation':False,'raw_restricted_data_used':False}
    (HERE/'results/runtime_provenance.json').write_text(json.dumps(report,indent=2)+'\n')
    (LOCAL/'java-path.txt').write_text(str(java[0]))
    print(json.dumps({'status':report['status'],'java_ready':True}),flush=True)

if __name__=='__main__':main()
