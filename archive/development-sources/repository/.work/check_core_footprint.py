import ast,re,sys
from pathlib import Path
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
from shapely.geometry import Polygon
from shapely.ops import unary_union
s=Path('working/Dara-Photo-Frame.scad').read_text()
def polys(name):
    body=s.split('module '+name+'() {',1)[1].split('\nmodule ',1)[0]
    out=[]
    for a,b in re.findall(r'polygon\(points = (\[.*?\]), paths = (\[.*?\]), convexity',body,re.S):
        pts=ast.literal_eval(a); paths=ast.literal_eval(b)
        out.append(Polygon([pts[i] for i in paths[0]],[[pts[i] for i in p] for p in paths[1:]]))
    return unary_union(out)
k=polys('knot_outline'); f=polys('fabric_outline').buffer(.15,join_style=2); m=polys('letter_outline')
core=unary_union([k,f,m])
print('Backing footprint valid:',core.is_valid,'connected:',core.geom_type)
print('Photo opening intersections with added core (mm2):',[round(unary_union([f,m]).intersection(polys('photo_loop_'+str(i))).area*.75**2,6) for i in range(1,9)])
r=Path('reference/Dara-Clean-Reference.scad').read_text()
for name in ['knot_outline','fabric_outline','letter_outline']:
    a=s.split('module '+name+'() {',1)[1].split('\nmodule ',1)[0].strip()
    b=r.split('module '+name+'() {',1)[1].split('\nmodule ',1)[0].strip()
    print(name,'unchanged:',a==b)
