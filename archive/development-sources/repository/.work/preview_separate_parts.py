import subprocess
p=subprocess.run([r'C:\Program Files (x86)\OpenSCAD\openscad.exe','--hardwarnings','-D','view_mode="exploded"','--preview','--imgsize=1000,1000','--camera=0,0,0,30,0,20,3000','--autocenter','--viewall','--projection=o','-o','.work/separate-parts-preview.png','working/Dara-Photo-Frame.scad'],capture_output=True,text=True)
print(p.returncode,p.stderr,flush=True)
