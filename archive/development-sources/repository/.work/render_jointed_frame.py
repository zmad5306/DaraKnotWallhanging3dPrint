from pathlib import Path
import subprocess, concurrent.futures, json, time, sys
EXE=r'C:\Program Files (x86)\OpenSCAD\openscad.exe'
SCAD='working/Dara-Photo-Frame-A1-Jointed.scad'
def run(i):
    start=time.monotonic()
    if i==0:
        args=['--preview','--imgsize=1600,1600','--camera=0,0,0,0,0,0,2800','--projection=o','-D','show_section_ids=true','-o','.work/jointed-assembly.png']
    else:
        args=['--camera=0,0,0,0,0,0,700','-D','view_mode="section"','-D',f'section_index={i}','--export-format=binstl','-o',f'.work/jointed-F{i}.stl']
    p=subprocess.run([EXE,'--hardwarnings',*args,SCAD],capture_output=True,text=True,timeout=600)
    r={'section':i,'seconds':time.monotonic()-start,'returncode':p.returncode,'stderr':p.stderr}
    Path(f'.work/jointed-F{i}-log.json').write_text(json.dumps(r,indent=2))
    print(i,p.returncode,round(r['seconds'],1),p.stderr if p.returncode else '',flush=True)
    return r
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
    tasks=list(range(1,int(sys.argv[1])+1)) if len(sys.argv)>1 else list(range(1,31))+[0]
    results=list(pool.map(run,tasks))
assert all(r['returncode']==0 and 'ERROR:'not in r['stderr'] and 'WARNING:'not in r['stderr']for r in results)
