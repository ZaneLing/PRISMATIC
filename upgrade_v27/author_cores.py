"""Load pinned author classes without unrelated example-data/DNC imports.

Class/function ASTs are unchanged. This is dependency isolation, not a claim
that new preprocessing, budgets or molecular resources reproduce paper scores.
"""
import ast, hashlib, importlib.util, math, sys
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from torch.nn.parameter import Parameter
from rdkit import Chem

ROOT=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources'
SAFE=Path('/tmp/prismatic-safedrug')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def armr():
    source=ROOT/'ARMR2025/code/net_mynet.py'
    assert sha(source)=='0355c90f3f56b165ab2ddd261a0defd36de9004c36aaaa65d6a4d0e2cfa1b680'
    spec=importlib.util.spec_from_file_location('pinned_armr2025',source)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
    spec.loader.exec_module(module);return module

def selected_definitions(path,names,namespace):
    tree=ast.parse(path.read_text());nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
    assert {n.name for n in nodes}==set(names)
    module=ast.Module(body=nodes,type_ignores=[])
    exec(compile(module,str(path),'exec'),namespace)

def safedrug():
    # Pinned repository identity and full-file hashes are also recorded by probe.
    import subprocess
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=SAFE,text=True).strip()=='88ce5c377dcdc2aa01aaa88f5478dfa4373ba49a'
    assert not subprocess.check_output(['git','diff','--','src/models.py','src/layers.py','src/util.py'],cwd=SAFE,text=True).strip()
    scope={'torch':torch,'nn':nn,'F':F,'np':np,'math':math,'Parameter':Parameter,'defaultdict':defaultdict,'Chem':Chem}
    selected_definitions(SAFE/'src/layers.py',['GraphConvolution'],scope)
    selected_definitions(SAFE/'src/models.py',['GCN','MaskLinear','MolecularGraphNeuralNetwork','SafeDrugModel','GAMENet'],scope)
    selected_definitions(SAFE/'src/util.py',['create_atoms','create_ijbonddict','extract_fingerprints','buildMPNN'],scope)
    return SimpleNamespace(**scope)
