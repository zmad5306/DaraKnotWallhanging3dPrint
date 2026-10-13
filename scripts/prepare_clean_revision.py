"""Preserve a fresh local baseline before rebuilding a delivered clean package.

Never overwrite an existing baseline: its matching artifacts are the evidence
for the current revision. Start from a fresh checkout/folder for a later edit.
"""
import shutil
from validate_print_project import ROOT,CAD,PACKAGE,STLS

def main():
    work=ROOT/'.work/edge-quality'
    targets=['baseline.scad','baseline-continuous.scad','baseline.3mf','baseline.json','baseline-stls']
    assert not any((work/n).exists() for n in targets),'A baseline already exists; do not replace active revision evidence.'
    work.mkdir(parents=True,exist_ok=True)
    for source,name in [(CAD,'baseline.scad'),(ROOT/'working/Dara-Photo-Frame.scad','baseline-continuous.scad'),
                        (PACKAGE/'Dara-Photo-Frame-A1-Complete.3mf','baseline.3mf'),(PACKAGE/'project-validation.json','baseline.json')]:
        shutil.copy2(source,work/name)
    shutil.copytree(STLS,work/'baseline-stls')
    print('Preserved matching CAD, STLs and Bambu project in',work)

if __name__=='__main__':main()
