from pathlib import Path
import subprocess, concurrent.futures
EXE=r'C:\Program Files (x86)\OpenSCAD\openscad.exe'
BASE=[EXE,'--hardwarnings','--camera=0,0,0,0,0,0,700']
SCAD='working/Dara-Photo-Frame-A1-Jointed.scad'
def run(i):
    p=subprocess.run(BASE+['-D','view_mode="section"','-D','part_family="M"','-D',f'section_index={i}','--export-format=binstl','-o',f'.work/jointed-M{i}.stl',SCAD],capture_output=True,text=True,timeout=180)
    print(i,p.returncode,p.stderr,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:list(pool.map(run,[1,2,3,4,5,6]))
