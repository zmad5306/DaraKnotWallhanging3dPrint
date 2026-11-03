from pathlib import Path
import subprocess, concurrent.futures, json, sys

EXE=r'C:\Program Files (x86)\OpenSCAD\openscad.exe'
SCAD='working/Dara-Photo-Frame-A1-Jointed.scad'
OUT=Path('working/review/photo-retainers')
OUT.mkdir(parents=True,exist_ok=True)
jobs={
 'screw-cutaway':('5,0,5,110,0,205,105',['view_mode="retainer_detail"']),
 'tab-closed':('4,0,4,180,0,0,100',['view_mode="retainer_detail"','retainer_cutaway=false']),
 'tab-open':('4,0,4,180,0,0,100',['view_mode="retainer_detail"','retainer_cutaway=false','retainers_open=true']),
 'fit-sample':('0,8,4,45,0,0,170',['view_mode="fit_sample"']),
 'tab-print':('0,0,1.5,40,0,25,65',['view_mode="retainer"']),
}
if '--all' in sys.argv:
    jobs.update({
      'assembly-rear':('0,0,8,155,0,20,2800',[]),
      'assembly-front':('0,0,8,0,0,0,2800',[]),
      'F5-rear':('0,0,7,135,0,25,670',['view_mode="section"','section_index=5']),
      'assembly-open':('0,0,8,180,0,0,2800',['retainers_open=true']),
    })
def run(item):
    name,(cam,defs)=item
    args=[EXE,'--hardwarnings','--preview','--imgsize=1400,1050','--projection=o','--camera='+cam]
    for d in defs:args+=['-D',d]
    p=subprocess.run(args+['-o',str(OUT/(name+'.png')),SCAD],capture_output=True,text=True,timeout=360)
    ok=p.returncode==0 and 'WARNING:'not in p.stderr and 'ERROR:'not in p.stderr
    print(name,'PASS'if ok else 'FAIL',p.stderr if not ok else '',flush=True)
    return {'view':name,'ok':ok,'stderr':p.stderr}
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
    results=list(pool.map(run,jobs.items()))
Path('.work/photo-retainers/preview-checks.json').write_text(json.dumps(results,indent=2))
assert all(r['ok']for r in results)
