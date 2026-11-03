from pathlib import Path
import subprocess, concurrent.futures, json, time
EXE=r'C:\Program Files (x86)\OpenSCAD\openscad.exe'
tasks={
 'original-frame':['-D','view_mode="frame"','-o','.work/jointed-original-frame.off','working/Dara-Photo-Frame.scad'],
 'original-M':['-D','view_mode="M"','-o','.work/jointed-original-M.off','working/Dara-Photo-Frame.scad'],
 'jointed-M':['-D','view_mode="M"','-o','.work/jointed-M.off','working/Dara-Photo-Frame-A1-Jointed.scad'],
 'preview':['--preview','--imgsize=1500,1500','--camera=0,0,0,0,0,0,2800','--autocenter','--viewall','--projection=o','-D','show_section_ids=true','-o','.work/jointed-assembly.png','working/Dara-Photo-Frame-A1-Jointed.scad'],
}
def run(item):
    name,args=item;start=time.monotonic()
    p=subprocess.run([EXE,'--hardwarnings','--camera=0,0,0,0,0,0,2800',*args],capture_output=True,text=True,timeout=900)
    result={'name':name,'seconds':time.monotonic()-start,'returncode':p.returncode,'stderr':p.stderr,'stdout':p.stdout}
    Path('.work/jointed-'+name+'-log.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result),flush=True)
    return result
tasks.pop('preview')
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    results=list(pool.map(run,tasks.items()))
assert all(r['returncode']==0 and 'ERROR:' not in r['stderr'] and 'WARNING:' not in r['stderr']for r in results)

