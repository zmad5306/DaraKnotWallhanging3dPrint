from pathlib import Path
import json,sys,zipfile,xml.etree.ElementTree as E,time
import numpy as np
import trimesh
import manifold3d as mf
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from development_3mf import solid
W=Path(__file__).resolve().parent
C='{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
SOURCE=Path(r'C:\Users\Zach\Downloads\Sanding_Block.3mf')
z=zipfile.ZipFile(SOURCE)
cfg=E.fromstring(z.read('Metadata/model_settings.config'))
root=E.fromstring(z.read('3D/3dmodel.model'))
def tf(s):
 t=np.eye(4);t[:3]=np.array(list(map(float,s.split()))).reshape(4,3).T;return t
poses={int(e.get('objectid')):tf(e.get('transform')) for e in root.find(C+'build')}
parts={};positions={}
for o in cfg.findall('object'):
 p={m.get('key'):m.get('value') for m in o.find('part').findall('metadata')}
 name=p['name'].replace('.stl','')
 mesh=trimesh.load_mesh(ROOT/'.work/sanding-block'/p['name'])
 off=np.array([float(p['source_offset_'+a]) for a in 'xyz'])
 if name=='Screw':
  R=poses[int(o.get('id'))][:3,:3]
  v=mesh.vertices@R.T
  cap=v[v[:,2]>v[:,2].max()-.002]
  center=(cap.min(0)+cap.max(0))/2
  top_axis=R.T@np.array([0,0,1]); top_center=R.T@center+off
  print('TOP AXIS',top_axis,'CENTER',top_center,'cap points',len(cap),flush=True)
 mesh.apply_translation(off)
 parts[name]=solid(mesh);positions[name]=mesh
def rotate_about(m,angle,axis,point):
 t=trimesh.transformations.rotation_matrix(np.radians(angle),axis,point)
 return m.transform(t[:3])
rear_center=np.array([0,-11.5,14.336305975914001])
results={}
for name, moving,fixed,axis,center in [
 ('rear',parts['Nut'],parts['Tighteneer'],np.array([1,0,0]),rear_center),
 ('top',parts['Screw'],parts['Base'],top_axis,top_center)]:
 samples=[]
 for angle in range(0,360,15):
  vol=(rotate_about(moving,angle,axis,center)^fixed).volume()
  samples.append([angle,vol])
  print(name,angle,vol,flush=True)
 results[name]=dict(axis=axis.tolist(),center=center.tolist(),rotation_intersections=samples)
(W/'source-motion-audit.json').write_text(json.dumps(results,indent=2))
