from pathlib import Path
import subprocess, concurrent.futures
OUT=Path('working/review/wall-blocks');CAD=Path('working/Dara-Photo-Frame-A1-Jointed.scad');EXE=r'C:\Program Files (x86)\OpenSCAD\openscad.exe'
import re
render_source=re.sub(r'^\$vp[trd] = .*?;.*$', '', CAD.read_text(), flags=re.M)
render_path=Path('.work/wall-blocks-screwed/render.scad');render_path.write_text(render_source);CAD=render_path
jobs=[
 ('assembly-rear','assembly','0,0,0,180,0,180,2500',[]),
 ('blocks-keys','wall_blocks','0,0,0,45,0,20,500',[]),
 ('block-rear','wall_block','0,0,0,150,0,180,360',[]),
 ('mount-exploded','wall_mount_detail','0,0,0,135,0,30,360',[]),
 ('keyhole-cutaway','wall_keyhole_detail','0,0,0,75,0,80,120',[]),
 ('fit-sample','wall_fit_sample','0,0,0,45,0,20,450',[]),
]
def run(job):
 name,view,cam,extra=job
 if '--blocks-only' in __import__('sys').argv and name in ['assembly-rear','mount-exploded']:return
 args=[EXE,'--hardwarnings','--camera='+cam,'--imgsize=1400,1000','--projection=o','--autocenter','--viewall','--colorscheme=Tomorrow','-o',str(OUT/(name+'.png')),'-D',f'view_mode="{view}"',*extra,str(CAD)]
 p=subprocess.run(args,capture_output=True,text=True,timeout=240)
 Path('.work/wall-blocks/'+name+'-png.log').write_text(p.stderr)
 assert p.returncode==0 and 'WARNING:'not in p.stderr and 'ERROR:'not in p.stderr,(name,p.stderr)
 print(name,'rendered',flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:list(pool.map(run,jobs))
