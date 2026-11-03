from pathlib import Path
import subprocess, concurrent.futures
exe=r'C:\Program Files (x86)\OpenSCAD\openscad.exe'
src='working/Dara-Photo-Frame.scad'
def run(job):
    name,args=job
    p=subprocess.run([exe,'--hardwarnings','-D','view_mode="frame"',*args,src],capture_output=True,text=True)
    print(name,p.returncode,p.stderr,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    list(pool.map(run,[('angle',['--preview','--imgsize=1100,1100','--camera=0,0,0,45,0,25,3000','--autocenter','--viewall','--projection=o','-o','.work/print-core-angle.png']),('geometry',['-o','.work/print-core-check.off'])]))
