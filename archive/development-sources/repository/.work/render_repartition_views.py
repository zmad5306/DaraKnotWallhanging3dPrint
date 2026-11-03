from pathlib import Path
import subprocess,concurrent.futures
cad=Path('working/Dara-Photo-Frame-A1-Jointed.scad');out=Path('.work/repartition')
jobs=[('frame-preview','frame','frame',1),('M-preview','M','M',1),('assembly-preview','assembly','frame',1),('largest-on-plate','section','frame',6),('frame-plates','layout','frame',1)]
def run(job):
 name,view,family,index=job
 args=[r'C:\Program Files (x86)\OpenSCAD\openscad.exe','--hardwarnings','--camera=0,0,0,0,0,0,2500','--imgsize=1400,1300','--projection=o','--autocenter','--viewall','--colorscheme=Tomorrow','-o',str(out/(name+'.png')),'-D',f'view_mode="{view}"','-D',f'part_family="{family}"','-D',f'section_index={index}','-D','show_section_ids=true','-D','show_plate_outline=true','-D','show_mount_hardware=false','-D','show_photo_hardware=false',str(cad)]
 p=subprocess.run(args,capture_output=True,text=True,timeout=180);(out/(name+'.log')).write_text(p.stderr);assert p.returncode==0 and 'ERROR:'not in p.stderr and 'WARNING:'not in p.stderr,(name,p.stderr)
 print(name,'rendered',flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:list(pool.map(run,jobs))
