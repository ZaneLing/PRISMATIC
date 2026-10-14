"""Resolve public CID/ATC molecular metadata; never transmit patient data."""
import csv, hashlib, json, re, time, urllib.request
from collections import defaultdict
from pathlib import Path
from rdkit import Chem

HERE = Path(__file__).resolve().parent
RESOURCE = Path.home() / 'Desktop/PRISMATIC/upgrade_v2/.local/resources'
OUT = RESOURCE / 'v27-molecules'
SOURCE = Path('/tmp/prismatic-safedrug/data/input/drug-atc.csv')
EXPECTED = 'b4d770a02d293f0726cc7dcbcd49e4a8a6b706d00f4a1d37498386eda76b7d9e'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, value): p.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

def main():
    assert sha(SOURCE) == EXPECTED
    OUT.mkdir(parents=True, exist_ok=True); (HERE/'results').mkdir(exist_ok=True)
    mapping = defaultdict(set)
    for row in csv.reader(SOURCE.open()):
        assert re.fullmatch(r'CID0\d+', row[0]), 'Unexpected identifier convention; stop rather than guess PubChem CID'
        cid = int(row[0][3:])
        for code in row[1:]:
            if re.fullmatch(r'[A-Z]\d{2}[A-Z]{2}\d{2}', code): mapping[cid].add(code[:5])
    cids = sorted(mapping); properties = {}; failures = []
    for i in range(0, len(cids), 25):
        batch = cids[i:i+25]
        path = OUT / ('pubchem-' + hashlib.sha256(json.dumps(batch).encode()).hexdigest()[:16] + '.json')
        url = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/' + ','.join(map(str,batch)) + '/property/CanonicalSMILES/JSON'
        if not path.exists():
            error = None
            for attempt in range(3):
                try:
                    payload = urllib.request.urlopen(url, timeout=40).read()
                    parsed = json.loads(payload); assert 'PropertyTable' in parsed
                    path.write_bytes(payload); error = None; break
                except Exception as exc:
                    error = str(exc); time.sleep(1 + attempt)
            if error:
                failures.append({'cids':batch, 'error':error}); continue
            time.sleep(.25)
        parsed = json.loads(path.read_bytes())
        for entry in parsed['PropertyTable']['Properties']:
            assert entry['CID'] in batch
            properties[entry['CID']] = entry
        print(json.dumps({'resolved_public_cids':len(properties),'requested':len(cids)}), flush=True)
    molecules = defaultdict(dict); invalid = []
    for cid, entry in properties.items():
        smiles = entry.get('ConnectivitySMILES', entry.get('CanonicalSMILES'))
        mol = Chem.MolFromSmiles(smiles) if smiles else None
        if mol is None:
            invalid.append(cid); continue
        canonical = Chem.MolToSmiles(mol, isomericSmiles=False)
        for atc in mapping[cid]: molecules[atc][cid] = canonical
    save(OUT/'atc4_molecules.json', {c:[{'cid':cid,'smiles':s} for cid,s in sorted(items.items())] for c,items in sorted(molecules.items())})
    all_classes = sorted({c for values in mapping.values() for c in values})
    report = {'status':'complete' if not failures and set(properties)==set(cids) and not invalid else 'incomplete',
      'cid_atc_sha256':sha(SOURCE), 'requested_public_cids':len(cids), 'returned_public_cids':len(properties),
      'classes_in_mapping':len(all_classes), 'classes_with_valid_molecules':len(molecules),
      'classes_without_valid_molecules':sorted(set(all_classes)-set(molecules)),
      'invalid_molecule_cids':invalid, 'unreturned_cids':sorted(set(cids)-set(properties)), 'request_failures':failures,
      'atc4_molecules_sha256':sha(OUT/'atc4_molecules.json'),
      'raw_response_sha256':{p.name:sha(p) for p in sorted(OUT.glob('pubchem-*.json'))},
      'scope':'Public class-level molecular metadata only. Compatibility with a particular training vocabulary must be checked separately; this does not yet reproduce SafeDrug.',
      'api_fields':'CanonicalSMILES endpoint currently returns ConnectivitySMILES; the returned field name is preserved in raw responses.',
      'restricted_data_sent':False}
    save(HERE/'results/molecular_resource_audit.json', report); print(json.dumps(report), flush=True)

if __name__ == '__main__': main()
