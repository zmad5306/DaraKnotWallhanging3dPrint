import subprocess
p=subprocess.run([r'C:\Program Files (x86)\OpenSCAD\openscad.exe','--hardwarnings','-D','view_mode="frame"','-D','show_knot=false','-D','show_fabric=false','--camera=0,0,0,0,0,0,3000','-o','.work/print-M-check.off','working/Dara-Photo-Frame.scad'],capture_output=True,text=True)
print(p.returncode,p.stderr,flush=True)
