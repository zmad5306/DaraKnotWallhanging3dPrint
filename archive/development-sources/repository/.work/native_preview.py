from pathlib import Path
import json, subprocess
d=json.loads(Path('.work/jointed-data.json').read_text())
colours=[[.72,.81,.85],[.92,.74,.51],[.65,.76,.58],[.82,.64,.69],[.66,.67,.84],[.89,.85,.64]]
body=[]
for family,info in d.items():
    for i,(g,p)in enumerate(zip(info['parts'],info['placements'])):
        shift=0
        if family=='frame':
            import sys
            sys.path.insert(0,str(Path('.work/python-libs').resolve()))
            import trimesh
            # min Z was moved to zero; this part's Z span distinguishes tracks.
            m=trimesh.load_mesh(f'.work/jointed-F{i+1}.stl')
            shift=3.2 if m.extents[2]>15 else 0
        fn=Path(f'.work/jointed-{family[0]}{i+1}.stl').resolve().as_posix().replace('jointed-f','jointed-F')
        body.append(f'color({colours[i%6]}) translate([0,0,{13.5 if family=="M" else 0}]) rotate([0,0,{-p["angle"]}]) translate([{p["centre"][0]},{p["centre"][1]},{-shift}]) import("{fn}",convexity=50);')
body.append('scale([.75,.75,.75]) { color(backer_colour) for(i=[0:7]) photo_backer(i); color(retainer_colour) for(i=[0:7],j=[0:3]) at_retainer(i,j) slider_mm(); }')
source=Path('working/Dara-Photo-Frame.scad').read_text().replace('scale([uniform_scale,uniform_scale,uniform_scale]) working_model();','\n'.join(body))
Path('.work/verified-assembly.scad').write_text(source)
for view,cam in [('front','0,0,0,0,0,0,2600'),('angle','0,0,0,28,0,22,2600')]:
    p=subprocess.run([r'C:\Program Files (x86)\OpenSCAD\openscad.exe','--hardwarnings','--preview','--imgsize=1300,1300','--camera='+cam,'--projection=o','-o',f'.work/jointed-verified-{view}.png','.work/verified-assembly.scad'],capture_output=True,text=True,timeout=60)
    print(view,p.returncode,p.stderr,flush=True)

