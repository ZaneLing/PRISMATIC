"""Apply the supplied AAMAS class to the current English manuscript in place.

Embedding the unmodified class through filecontents keeps the desktop editor's
single-file compiler usable. Original class notices are retained verbatim.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile


def apply(archive: Path, manuscript: Path):
    with ZipFile(archive) as z:
        cls = z.read("aamas.cls")
        original = z.read("prismatic_arxiv.tex").decode()
    assert r"\documentclass[sigconf,nonacm]{aamas}" in original
    source = manuscript.read_text()
    marker = "% PRISMATIC MANUSCRIPT START"
    if marker in source:
        source = source.split(marker, 1)[1]
    abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", source, re.S).group(1)
    body = source[source.index(r"\section{Introduction}"):]
    body = body.replace(r"\begin{table}[t]", r"\begin{table*}[t]")
    body = body.replace(r"\end{table}", r"\end{table*}")
    header = r"""% PRISMATIC MANUSCRIPT START
\documentclass[sigconf,nonacm]{aamas}
\usepackage{tabularx,array,multirow}
\usepackage{balance}
\settopmatter{printacmref=false}
\setcopyright{none}
\title[PRISMATIC]{PRISMATIC: A Time-Frozen, Method-Level Evaluation Protocol for Evolving Prescription Support}
\subtitle{Research draft v0.4-dev --- 14 October 2026}
\author{Ziyang Ling}
\email{zaneling@mail.ustc.edu.cn}
\affiliation{\institution{University of Science and Technology of China}\country{China}}
\author{Shuyu Lu}
\email{Shuyu.Lu@uth.tmc.edu}
\affiliation{\institution{The University of Texas Health Science Center at Houston}\country{United States}}
\begin{abstract}
"""
    after = r"""
\end{abstract}
\keywords{Prescription support, medication recommendation, multi-agent systems, experience learning, clinical evaluation}
\begin{document}
\pagestyle{fancy}
\fancyhead{}
\maketitle

"""
    prefix = ("% AAMAS class embedded unchanged from the user-supplied ZIP for standalone compilation.\n"
              "% Jump to PRISMATIC MANUSCRIPT START below for the editable manuscript.\n"
              + r"\begin{filecontents*}[overwrite]{aamas.cls}" + "\n"
              + cls.decode() + "\n" + r"\end{filecontents*}" + "\n")
    manuscript.write_text(prefix + header + abstract.strip() + after + body)
    provenance = {
        "archive_filename": archive.name,
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "class_member": "aamas.cls",
        "class_sha256": hashlib.sha256(cls).hexdigest(),
        "template_member": "prismatic_arxiv.tex",
        "options": "sigconf,nonacm",
        "class_modifications": "none; original class embedded using filecontents for single-file compiler",
        "author_source": "author names and institutions from supplied prismatic_arxiv.tex",
        "active_manuscript": str(manuscript.relative_to(Path(__file__).resolve().parents[2])),
    }
    (manuscript.parent / "template_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--manuscript", type=Path, required=True)
    a = p.parse_args()
    apply(a.archive, a.manuscript)
