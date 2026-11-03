from pathlib import Path
import subprocess,concurrent.futures,json
EXE=r'C:\Program Files (x86)\OpenSCAD\openscad.exe'
SCAD='working/Dara-Photo-Frame-A1-Jointed.scad'
tasks={
 'assembly': ['--preview','--imgsize=1400,1400','--camera=0,0,0,28,0,22,2800','--projection=o','-o','.work/final-jointed-assembly.png'],
 'frame-joint':['--preview','--imgsize=1100,800','--camera=5,0,6,60,0,30,230','--projection=o','-D','view_mode="joint_detail"','-o','.work/final-frame-joint.png'],
 'M-joint':['--preview','--imgsize=1100,800','--camera=5,0,6,60,0,30,150','--projection=o','-D','view_mode="joint_detail"','-D','part_family="M"','-o','.work/final-M-joint.png'],
 'F2-native':['--camera=0,0,0,0,0,0,700','-D','view_mode="section"','-D','section_index=2','--export-format=binstl','-o','.work/final-F2.stl'],
}
def run(item):
    name,args=item
    p=subprocess.run([EXE,'--hardwarnings',*args,SCAD],capture_output=True,text=True,timeout=180)
    r={'view':name,'returncode':p.returncode,'stderr':p.stderr}
    print(json.dumps(r),flush=True)
    return r
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:r=list(pool.map(run,tasks.items()))
assert all(x['returncode']==0 and 'WARNING:'not in x['stderr'] and 'ERROR:'not in x['stderr']for x in r)
Path('.work/final-cad-checks.json').write_text(json.dumps(r,indent=2))
