"""Create a current continuous artwork reference, retaining the historical source."""
import re,subprocess
from validate_print_project import ROOT,CAD
from rebuild_clean_cad import clean_shapes
from repair_curve_artifacts import serialize

def main():
    output=ROOT/'working/Dara-Clean-Artwork.scad'
    text=(output if output.exists() else ROOT/'reference/Dara-Clean-Reference.scad').read_text()
    knot,fabric,_,_=clean_shapes()
    for name,shape in [('knot_outline',knot),('fabric_outline',fabric)]:
        text,n=re.subn(r'module '+name+r'\(\) \{.*?\n\}',lambda _:serialize(name,shape),text,count=1,flags=re.S)
        assert n==1
    current=CAD.read_text()
    letter=re.search(r'module letter_outline\(\) \{.*?\n\}',current,re.S)[0]
    text,n=re.subn(r'module letter_outline\(\) \{.*?\n\}',lambda _:letter,text,count=1,flags=re.S)
    assert n==1
    note='// CURRENT CLEAN ARTWORK: tangent line/arc reconstruction, 2026-10-13.\n// Visual reference only. Use Dara-Photo-Frame-A1-Jointed.scad for manufacturing.\n'
    if not text.startswith(note):text=note+text
    output.write_text(text)
    command=[r'C:\Program Files (x86)\OpenSCAD\openscad.exe','--hardwarnings','--camera=0,0,0,0,0,0,700','-o',str(output.with_suffix('.svg')),'-D','view_mode="drawing"',str(output)]
    result=subprocess.run(command,capture_output=True,text=True,timeout=120)
    assert result.returncode==0 and 'WARNING:' not in result.stderr,result.stderr
    print(output)

if __name__=='__main__':main()
