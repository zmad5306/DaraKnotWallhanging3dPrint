import sys, json, math
from pathlib import Path
sys.path.insert(0, str(Path.cwd()/'scripts'))
from prepare_hammered_m_project import artwork, read_array, np
from shapely.geometry import Polygon, LineString, box, Point
from shapely import affinity
from scipy.spatial import Voronoi

dest=Path('C:/Users/Zach/.codex/visualizations/2026/10/14/01a139e6-6046-7663-8f27-6859b7d6a3bd')
cad=Path('working/Dara-Photo-Frame-A1-Jointed.scad').read_text()
outline=artwork(cad,'letter_outline').simplify(.1,preserve_topology=True)
joints=read_array(cad,'M_joints')

def path(g):
    if g.is_empty:return ''
    if hasattr(g,'geoms'):return ' '.join(path(a) for a in g.geoms)
    if g.geom_type=='Polygon':
        rings=[g.exterior,*g.interiors]
        return ' '.join('M'+' L'.join(f'{x:.2f},{y:.2f}' for x,y in r.coords)+' Z' for r in rings)
    if g.geom_type=='LineString':return 'M'+' L'.join(f'{x:.2f},{y:.2f}' for x,y in g.coords)
    return ''

def place(g,pos,angle):
    return affinity.translate(affinity.rotate(g,angle,origin=(0,0)),*pos)

actual=[]
for j in joints:
    # Intersect only the local joint neighborhood, excluding other strokes.
    segment=place(LineString([(0,-j[4]/2-18),(0,j[4]/2+18)]),j[2],j[3])
    actual.append(path(segment.intersection(outline)))

concept=[([32.336,136.583],57.061,29),([-32.336,136.583],122.939,29),
         ([-257,0],90,60),([257,0],90,60),([0,0],90,42)]
bands=[]; grooves=[]
for pos,angle,span in concept:
    bands.append(path(place(box(-6,-span,6,span),pos,angle).intersection(outline)))
    grooves.append(path(place(box(-.65,-span,.65,span),pos,angle).intersection(outline)))

# Schematic cells at the actual hammer-pattern spacing and random seed.
xmin,ymin,xmax,ymax=outline.bounds
rng=np.random.RandomState(73); centers=[]
for row in range(-2,int(np.ceil((ymax-ymin)/(9*.866)))+5):
    for col in range(-2,int(np.ceil((xmax-xmin)/9))+5):
        centers.append([(col-.5)*9+(row%2)*4.5+xmin+rng.uniform(-2.52,2.52),
                        (row-.5)*9*.866+ymin+rng.uniform(-2.52,2.52)])
vor=Voronoi(centers); cells=[]
for idx,ri in enumerate(vor.point_region):
    r=vor.regions[ri]
    if not r or -1 in r:continue
    g=Polygon(vor.vertices[r]).intersection(outline)
    if g.area>.5:cells.append([path(g),round(.06+.10*(idx%5)/4,3)])
payload={'outline':path(outline),'actual':actual,'bands':bands,'grooves':grooves,'cells':cells}
(dest/'m-joint-concepts-data.json').write_text(json.dumps(payload,separators=(',',':')),encoding='utf-8')
print(json.dumps({'cells':len(cells),'outline_bounds':outline.bounds,'bands':len(bands),'bytes':(dest/'m-joint-concepts-data.json').stat().st_size}))
