from pathlib import Path
import subprocess
out=Path('.work/repartition/native')
s=Path('working/Dara-Photo-Frame-A1-Jointed.scad').read_text().replace('sectioned_model();','')
for kind in ['frame','M']:
 src=out/f'original-{kind}.scad';src.write_text(s+f'\noriginal_body_mm("{kind}");\n')
 cmd=[r'C:\Program Files (x86)\OpenSCAD\openscad.exe','--hardwarnings','--camera=0,0,0,0,0,0,1000','--export-format=binstl','-o',str(out/f'original-{kind}.stl'),str(src)]
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
 (out/f'original-{kind}.log').write_text(p.stderr);assert p.returncode==0 and 'ERROR:'not in p.stderr and 'WARNING:'not in p.stderr,p.stderr
 print('Original body rendered:',kind,flush=True)
