"""Prepare actual ATC-L4 training graphs and molecular resources, without models."""
import csv,hashlib,json
from collections import defaultdict
from pathlib import Path
import joblib,numpy as np,pandas as pd
from rdkit import Chem
from rdkit.Chem import BRICS
from author_cores import safedrug,ROOT as RESOURCE
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v27'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
    protocol=json.loads((HERE/'training_addendum.json').read_text());assert sha(PRIVATE/'visits.joblib')==protocol['cohort_bundle_sha256']
    source=joblib.load(PRIVATE/'visits.joblib');vocab=source['vocab'];mols=json.loads((RESOURCE/'v27-molecules/atc4_molecules.json').read_text())
    ddi_path=RESOURCE/'drug-DDI.csv';assert sha(ddi_path)=='60bd3d071345473236f56638ebb732c3c964f0fd3468fdd29a444bcc1bf80d35'
    ddi=pd.read_csv(ddi_path);counts=ddi.groupby(['Polypharmacy Side Effect','Side Effect Name']).size().reset_index().rename(columns={0:'count'}).sort_values('count',ascending=False).reset_index(drop=True)
    selected=counts.iloc[-40:];pairs=ddi.merge(selected[['Side Effect Name']],on='Side Effect Name')[['STITCH 1','STITCH 2']].drop_duplicates()
    source_drugs=set(ddi['STITCH 1'])|set(ddi['STITCH 2']);mapping=defaultdict(set)
    for row in csv.reader(Path('/tmp/prismatic-safedrug/data/input/drug-atc.csv').open()):
        for code in row[1:]:
            if code[:5] in vocab['medications']:mapping[row[0]].add(code[:5])
    report={'status':'complete','ddi_source_sha256':sha(ddi_path),'selected_effect_groups':selected[['Polypharmacy Side Effect','Side Effect Name','count']].to_dict('records'),
      'selected_source_pairs':len(pairs),'panels':{},'training_addendum_sha256':sha(HERE/'training_addendum.json')}
    indexes={f:{c:i for i,c in enumerate(vocab[f])} for f in ['diagnoses','procedures']}
    for panel,meds in [('full',vocab['medications']),('molecular',[c for c in vocab['medications'] if c in mols])]:
        ci={c:i for i,c in enumerate(meds)};size=len(meds);d=np.zeros((size,size),dtype=np.float32);e=np.zeros_like(d)
        for a,b in pairs.itertuples(index=False,name=None):
            for x in mapping[a]:
                for y in mapping[b]:
                    if x in ci and y in ci and x!=y:d[ci[x],ci[y]]=d[ci[y],ci[x]]=1
        encoded={};stats={}
        for split,patients in source['data'].items():
            encoded[split]=[];removed=zero=targets=0
            for patient in patients:
                visits=[]
                for v in patient['visits']:
                    gold=v['medications'] if panel=='full' else [c for c in v['medications'] if c in ci]
                    removed+=len(v['medications'])-len(gold);zero+=not gold;targets+=len(gold)
                    visit={'case_id':v['case_id'],'gold':gold,'codes':[[indexes[f].get(c,len(indexes[f])) for c in v[f]] for f in ['diagnoses','procedures']]+[[ci[c] for c in v['medications'] if c in ci]]}
                    visits.append(visit)
                    if split=='train':e[np.ix_(visit['codes'][2],visit['codes'][2])]=1
                encoded[split].append({'subject_hash':patient['subject_hash'],'visits':visits})
            stats[split]={'patients':len(patients),'visits':sum(len(p['visits']) for p in patients),'gold_targets':targets,'excluded_by_declared_subspace':removed,'empty_targets':zero}
        np.fill_diagonal(e,0);covered=sorted({c for cid,classes in mapping.items() if cid in source_drugs for c in classes if c in ci})
        payload={'data':encoded,'medications':meds,'sizes':[len(vocab['diagnoses'])+1,len(vocab['procedures'])+1,size],'ddi':d,'ehr':e,'ddi_covered_indices':[ci[c] for c in covered]}
        if panel=='molecular':
            molecule={c:[x['smiles'] for x in mols[c]] for c in meds};frags={c:sorted({f for s in molecule[c] for f in BRICS.BRICSDecompose(Chem.MolFromSmiles(s))}) for c in meds}
            assert all(frags.values());all_frags=sorted({f for fs in frags.values() for f in fs});fi={f:i for i,f in enumerate(all_frags)}
            mask=np.zeros((size,len(all_frags)),dtype=np.float32)
            for c in meds:mask[ci[c],[fi[f] for f in frags[c]]]=1
            graphs,nfp,projection=safedrug().buildMPNN(molecule,dict(enumerate(meds)),device='cpu')
            assert len(graphs)==sum(len(x) for x in molecule.values()) and np.allclose(projection.sum(1),1)
            payload.update(mpnn_graphs=graphs,n_fingerprints=nfp,average_projection=projection,substructure_mask=mask)
            report['molecular_graphs']={'graphs':len(graphs),'fingerprints':nfp,'brics_fragments':len(all_frags),'minimum_fragments_per_class':int(mask.sum(1).min()),'total_atoms_with_H':sum(x[2] for x in graphs),'missing_projection_rows':int((projection.sum(1)==0).sum())}
        path=PRIVATE/(panel+'-models.joblib');joblib.dump(payload,path)
        report['panels'][panel]={'classes':size,'ddi_edges':int(d.sum()/2),'ehr_edges':int(e.sum()/2),'classes_in_ddi_source':len(covered),'splits':stats,'bundle_sha256':sha(path)}
        print(json.dumps({'panel':panel,**report['panels'][panel]}),flush=True)
    save(HERE/'results/model_resource_manifest.json',report)
if __name__=='__main__':main()
