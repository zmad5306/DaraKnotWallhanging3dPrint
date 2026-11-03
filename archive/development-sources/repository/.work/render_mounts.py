from pathlib import Path
import subprocess, concurrent.futures, json, time
EXE=r'C:\Program Files (x86)\OpenSCAD\openscad.exe'
SCAD='working/Dara-Photo-Frame-A1-Jointed.scad'
affected=json.loads(Path('.work/mount-affected.json').read_text())
jobs=[(family,i+1) for family,ids in affected.items() for i in ids]
def run(job):
    family,i=job; name=f'{family[0].upper()}{i}'; start=time.monotonic()
    args=['--camera=0,0,0,0,0,0,700','-D','view_mode="section"','-D',f'part_family="{family}"','-D',f'section_index={i}','--export-format=binstl','-o',f'.work/mounted-{name}.stl']
    p=subprocess.run([EXE,'--hardwarnings',*args,SCAD],capture_output=True,text=True,timeout=600)
    r={'part':name,'seconds':round(time.monotonic()-start,1),'returncode':p.returncode,'stderr':p.stderr}
    Path(f'.work/mounted-{name}-log.json').write_text(json.dumps(r,indent=2))
    ok=p.returncode==0 and 'ERROR:' not in p.stderr and 'WARNING:' not in p.stderr
    print(name, 'PASS' if ok else 'FAIL',r['seconds'],'' if ok else p.stderr,flush=True)
    return ok
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    results=list(pool.map(run,jobs))
assert all(results)
