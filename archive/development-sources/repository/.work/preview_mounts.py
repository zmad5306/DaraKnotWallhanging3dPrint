from pathlib import Path
import subprocess,json,concurrent.futures,time
EXE=r'C:\Program Files (x86)\OpenSCAD\openscad.exe'
SCAD='working/Dara-Photo-Frame-A1-Jointed.scad'
jobs={
 'assembly':['--camera=0,0,0,28,0,22,2800'],
 'screw-cutaway':['--camera=0,0,12,68,0,20,145','-D','view_mode="mount_detail"'],
 'screw-exploded':['--camera=0,0,12,60,0,25,165','-D','view_mode="mount_detail"','-D','mount_cutaway=false','-D','mount_explode=12'],
 'M-rear':['--camera=0,0,0,180,0,0,1550','-D','view_mode="M"'],
 'map':['--camera=0,0,0,0,0,0,1650','-D','view_mode="mount_map"'],
 'washer':['--camera=0,0,0,60,0,30,35','-D','view_mode="washer"'],
}
def run(item):
    name,args=item;start=time.monotonic()
    p=subprocess.run([EXE,'--hardwarnings','--preview','--imgsize=1300,1000','--projection=o',*args,'-o',f'.work/mount-preview-{name}.png',SCAD],capture_output=True,text=True,timeout=240)
    ok=p.returncode==0 and 'WARNING:' not in p.stderr and 'ERROR:' not in p.stderr
    print(name,'PASS' if ok else 'FAIL',round(time.monotonic()-start,1),p.stderr,flush=True)
    return {'name':name,'ok':ok,'stderr':p.stderr}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,jobs.items()))
Path('.work/mount-preview-checks.json').write_text(json.dumps(results,indent=2))
assert all(r['ok']for r in results)
