from pathlib import Path
import subprocess,concurrent.futures,json,time
root=Path.cwd(); exe=r'C:\Program Files (x86)\OpenSCAD\openscad.exe'; scad=root/'working/Dara-Photo-Frame.scad'
jobs={
'back': ['--preview','--imgsize=1400,1400','--camera=0,0,0,0,180,0,3000','--autocenter','--viewall','--projection=o','--colorscheme=Tomorrow','-o',str(root/'.work/photo-back.png')],
'detail': ['-D','view_mode="fit_sample"','--preview','--imgsize=1200,900','--camera=0,0,0,45,180,25,100','--autocenter','--viewall','--projection=o','--colorscheme=Tomorrow','-o',str(root/'.work/photo-detail.png')],
'slider':['-D','view_mode="retainer"','--camera=0,0,0,0,0,0,100','--export-format=binstl','-o',str(root/'.work/photo-slider.stl')],
'frame':['-D','view_mode="frame"','-D','show_fabric=false','-D','show_letter=false','--camera=0,0,0,0,0,0,3000','--export-format=binstl','-o',str(root/'.work/photo-frame-sliders.stl')],
'backer':['-D','view_mode="backer"','--camera=0,0,0,0,0,0,3000','--export-format=binstl','-o',str(root/'.work/photo-backer.stl')]}
def run(item):
 name,args=item;t=time.time();p=subprocess.run([exe,'--hardwarnings',*args,str(scad)],capture_output=True,text=True,timeout=900)
 r=dict(name=name,seconds=round(time.time()-t,1),code=p.returncode,log=p.stderr);print(json.dumps(r),flush=True);return r
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:r=list(pool.map(run,jobs.items()))
(root/'.work/photo-render-checks.json').write_text(json.dumps(r,indent=2))
