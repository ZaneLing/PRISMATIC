"""Post-execution provenance inventory, never described as a preregistration."""
import json,subprocess,time
from common import *
def main():
    labels=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/rxrsi-v45/full_labels'
    sources={name:subprocess.check_output(['git','-C',str(RESOURCES/path),'rev-parse','HEAD'],text=True).strip() for name,path in [('SkeMex','SkeMex'),('FLAME','FLAME')]}
    source_hashes={str(p.relative_to(HERE)):sha(p) for p in sorted(HERE.glob('*.py'))}
    label_hashes={p.name:sha(p) for p in sorted(labels.glob('*.json'))}
    versions={}
    for interpreter,label in [(Path.home()/'Desktop/PRISMATIC/upgrade_v2/.venv-llm/bin/python','local_llm'),(Path.home()/'Desktop/PRISMATIC/upgrade_v2/.venv/bin/python','analysis')]:
        program='import sys,json,importlib.metadata as m\npackages='+repr(['mlx','mlx-lm','transformers','numpy'] if label=='local_llm' else ['numpy','scikit-learn','torch','matplotlib'])+'\nprint(json.dumps({"python":sys.version,"packages":{k:m.version(k) for k in packages}}))'
        versions[label]=json.loads(subprocess.check_output([str(interpreter),'-c',program],text=True))
    save(HERE/'results/execution_manifest.json',{'recorded_unix':time.time(),'inventory_timing':'post-execution; not preregistration',
       'python_sources_sha256':source_hashes,'author_repositories':sources,'runtime':versions,
       'label_snapshot_files':len(label_hashes),'label_snapshot_sha256':digest(label_hashes),
       'case_source_sha256':sha(PRIVATE/'cases.json'),'paid_model_api_cost_usd':0,'external_patient_requests':0})
    print('Recorded aggregate execution provenance')
if __name__=='__main__':main()
