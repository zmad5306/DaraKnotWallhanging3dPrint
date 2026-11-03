from pathlib import Path
import subprocess, concurrent.futures, json, time

EXE = r'C:\Program Files (x86)\OpenSCAD\openscad.exe'
SCAD = 'working/Dara-Photo-Frame-A1-Jointed.scad'
OUT = Path('.work/photo-retainers')
OUT.mkdir(exist_ok=True)
jobs = [(f'F{i}', ['view_mode="section"', f'section_index={i}']) for i in range(1,31)]
jobs += [('tab', ['view_mode="retainer"']), ('fit-sample', ['view_mode="fit_sample"'])]
jobs += [('fit-frame', ['view_mode="fit_sample"', 'show_backers=false', 'show_retainers=false'])]
jobs += [('tab-thin', ['view_mode="retainer"', 'photo_retainer_thickness=2.5']),
         ('tab-thick', ['view_mode="retainer"', 'photo_retainer_thickness=4']),
         ('fit-frame-thin', ['view_mode="fit_sample"', 'show_backers=false', 'show_retainers=false', 'photo_retainer_thickness=2.5', 'photo_pilot_diameter=3.3'])]

def run(job):
    name,defs=job
    start=time.monotonic()
    args=[EXE,'--hardwarnings','--camera=0,0,0,0,0,0,700','--export-format=binstl','-o',str(OUT / (name+'.stl'))]
    for d in defs: args+=['-D',d]
    p=subprocess.run(args+[SCAD],capture_output=True,text=True,timeout=600)
    r={'part':name,'seconds':round(time.monotonic()-start,1),'returncode':p.returncode,'stderr':p.stderr}
    (OUT/(name+'-log.json')).write_text(json.dumps(r,indent=2))
    ok=p.returncode==0 and 'ERROR:'not in p.stderr and 'WARNING:'not in p.stderr
    print(name,'PASS' if ok else 'FAIL',r['seconds'],''if ok else p.stderr,flush=True)
    return ok

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    results=list(pool.map(run,jobs))
assert all(results)
