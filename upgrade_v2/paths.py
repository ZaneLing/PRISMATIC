"""Local paths for restricted derivatives and public model weights."""

import os
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
RESTRICTED_ROOT = Path(os.environ.get(
    "PRISMATIC_RESTRICTED_ROOT",
    str(Path.home() / "Desktop/MedTreeBench/dataset/restricted"),
)).expanduser()
ARTIFACT_DIR = Path(os.environ.get(
    "PRISMATIC_ARTIFACT_DIR",
    str(RESTRICTED_ROOT / "prismatic-v2"),
)).expanduser()
