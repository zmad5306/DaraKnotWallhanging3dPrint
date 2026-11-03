from pathlib import Path
import subprocess,concurrent.futures,json,time
EXE=r'C:\Program Files (x86)\OpenSCAD\openscad.exe'
SCAD='working/Dara-Photo-Frame-A1-Jointed.scad'
jobs={
 'screw-cutaway':['--camera=0,0,12,68,0,20,145','-D','view_mode="mount_detail"'],
 'M1-rear':['--camera=0,0,4,140,0,28,690','-D','view_mode="section"','-D','part_family="M"'],
 'assembly':['--camera=0,0,0,28,0,22,2800'],
 'mount-map':['--camera=0,0,0,0,0,0,1800','-D','view_mode="mount_map"'],
}
def run(item):
    name,args=item;start=time.monotonic()
    p=subprocess.run([EXE,'--hardwarnings','--preview','--imgsize=1300,1000','--projection=o',*args,'-o',f'.work/flat-preview-{name}.png',SCAD],capture_output=True,text=True,timeout=240)
    ok=p.returncode==0 and 'WARNING:'not in p.stderr and 'ERROR:'not in p.stderr
    print(name,'PASS'if ok else 'FAIL',round(time.monotonic()-start,1),p.stderr,flush=True)
    return {'view':name,'ok':ok,'stderr':p.stderr}
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:r=list(pool.map(run,jobs.items()))
Path('.work/flat-preview-checks.json').write_text(json.dumps(r,indent=2))
assert all(x['ok']for x in r)
