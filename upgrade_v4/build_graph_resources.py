"""Map author-linked TWOSIDES resource to ATC-L4; no clinical safety claim."""
from __future__ import annotations
import csv,json,hashlib
from pathlib import Path
from collections import defaultdict
import duckdb,numpy as np,pandas as pd
from build_protocol_data import ROOT,sha
from run_protocol_methods import take

HERE=Path(__file__).resolve().parent
RES=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources'

def run():
    classes=json.loads((HERE/'results/protocol_method_results.json').read_text())['classes'];ci={c:i for i,c in enumerate(classes)}
    mapping=defaultdict(set)
    source=Path('/tmp/prismatic-safedrug/data/input/drug-atc.csv')
    for row in csv.reader(source.open()):
        for code in row[1:]:
            if code[:5] in ci:mapping[row[0]].add(code[:5])
    pairs=pd.DataFrame([(cid,c) for cid,codes in mapping.items() for c in codes],columns=['cid','atc4'])
    con=duckdb.connect();con.register('map',pairs)
    # Keep the complete source pair relation. This differs from the paper's side-effect subset.
    con.execute('CREATE TEMP TABLE ddi AS SELECT * FROM read_csv(?)',[str(RES/'drug-DDI.csv')])
    edges=con.execute('''SELECT DISTINCT a.atc4 AS a,b.atc4 AS b FROM ddi d
       JOIN map a ON d."STITCH 1"=a.cid JOIN map b ON d."STITCH 2"=b.cid WHERE a.atc4<>b.atc4''').fetchall()
    adj=np.zeros((len(classes),len(classes)),dtype=np.float32)
    for a,b in edges:adj[ci[a],ci[b]]=adj[ci[b],ci[a]]=1
    frame=take(pd.read_parquet(ROOT/'prismatic-v4/cohort.parquet'),'train',40000)
    ehr=np.zeros_like(adj)
    for row in frame.atc4_codes:
        ix=[ci[c] for c in row if c in ci]
        ehr[np.ix_(ix,ix)]=1
    np.fill_diagonal(ehr,0)
    covered=sorted(set(pairs.atc4));seen_cids=set(con.execute('SELECT DISTINCT "STITCH 1" FROM ddi UNION SELECT DISTINCT "STITCH 2" FROM ddi').fetchnumpy()['STITCH 1'])
    source_covered=sorted({c for cid,codes in mapping.items() if cid in seen_cids for c in codes})
    con.close();np.savez_compressed(RES/'atc4_graphs.npz',ddi=adj,ehr=ehr)
    (RES/'atc4_cids.json').write_text(json.dumps({c:sorted(int(cid[3:]) for cid,codes in mapping.items() if c in codes) for c in classes},indent=2)+'\n')
    report={'run_id':'E01-atc4-graph-resources-r1','ddi_sha256':sha(RES/'drug-DDI.csv'),
       'cid_atc_sha256':sha(source),'graph_sha256':sha(RES/'atc4_graphs.npz'),'classes':classes,
       'classes_with_cid_mapping':len(covered),'classes_represented_in_source_ddi_drugs':len(source_covered),
       'classes_without_cid_mapping':sorted(set(classes)-set(covered)),
       'undirected_ddi_edges':int(adj.sum()/2),'undirected_ehr_edges':int(ehr.sum()/2),
       'scope':'all source TWOSIDES pairs aggregated to ATC-L4; not the original selected-side-effect protocol',
       'limits':['No recorded pair does not establish no interaction.','Class-level research graph is not an ingredient-level clinical rule base.',
         'Compound-to-class multiplicity broadens graph edges; report this adaptation.']}
    (HERE/'results/graph_resource_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':run()
