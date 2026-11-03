import sys, re, ast
from pathlib import Path
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
import trimesh
from shapely.geometry import Polygon
from shapely.validation import explain_validity
mesh=trimesh.load_mesh('.work/reference-bare.stl')
print('Bare mesh',mesh.bounds.tolist(),mesh.is_watertight,flush=True)
text=Path('reference/Dara-Clean-Reference.scad').read_text()
entries=re.findall(r'polygon\(points = (\[.*?\]), paths = (\[.*?\]), convexity',text,flags=re.S)
for i,(a,b) in enumerate(entries):
    pts=ast.literal_eval(a); paths=ast.literal_eval(b)
    poly=Polygon([pts[j] for j in paths[0]],[[pts[j] for j in path] for path in paths[1:]])
    print(i,len(pts),poly.area,explain_validity(poly),flush=True)
