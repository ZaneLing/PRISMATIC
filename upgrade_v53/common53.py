import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT/'upgrade_v52'))
from common52 import FIELDS,digest,sha,save,key,uniq,counts,metrics
HERE=Path(__file__).resolve().parent
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v53'
DEV=PRIVATE.parent/'prismatic-v52'
SOURCE=PRIVATE.parent/'prismatic-v25'
