from pathlib import Path
import subprocess,concurrent.futures,json
EXE=r'C:\Program Files (x86)\OpenSCAD\openscad.exe'
SCAD='working/Dara-Photo-Frame-A1-Jointed.scad'
D=json.loads(Path('.work/jointed-data.json').read_text())
jidx=next(i+1 for i,j in enumerate(D['frame']['joints']) if j['male']==4 or j['female']==4)
jobs={
 'M1-print':['--camera=0,0,8,45,0,28,690','-D','view_mode="section"','-D','part_family="M"'],
 'clearance-tuning':['--camera=0,0,0,25,0,25,2800','-D','dowel_clearance=.3','-D','dowel_slot_relief=1'],
 'lap-closeup':['--camera=5,0,6,60,0,30,230','-D','view_mode="joint_detail"','-D',f'joint_index={jidx}'],
 'mount-map':['--camera=0,0,0,0,0,0,1800','-D','view_mode="mount_map"'],
}
def run(item):
    name,args=item
    p=subprocess.run([EXE,'--hardwarnings','--preview','--imgsize=1300,1000','--projection=o',*args,'-o',f'.work/final-{name}.png',SCAD],capture_output=True,text=True,timeout=240)
    ok=p.returncode==0 and 'WARNING:' not in p.stderr and 'ERROR:' not in p.stderr
    print(name,'PASS' if ok else 'FAIL',p.stderr,flush=True)
    return {'name':name,'ok':ok,'stderr':p.stderr}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:r=list(pool.map(run,jobs.items()))
Path('.work/final-mount-checks.json').write_text(json.dumps(r,indent=2))
assert all(x['ok'] for x in r)
