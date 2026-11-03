exec((__import__('pathlib').Path(__file__).parent/'audit.py').read_text().split('results={}')[0])
from scipy.spatial import cKDTree
import hashlib
ns={'__file__':str(ROOT/'.work/sanding-block/finalize.py')}
exec((ROOT/'.work/sanding-block/finalize.py').read_text().split("path=OUT/")[0],ns)
S=228.6/162.5
old=ns['read_geometry'](ns['load'](ROOT/'.work/sanding-block/editable-validated.3mf'))
current=ns['read_geometry'](ns['load'](ROOT/'output/Sanding-Block-Quarter-Sheet-A1-PETG/Sanding-Block-Quarter-Sheet-A1-PETG-r1.3mf'))
out={}
for name in old:
 a=old[name];b=current[name]
 # Compare translation-invariant bed-oriented shape; user may move objects.
 va=a.vertices-a.bounds.mean(0);vb=b.vertices-b.bounds.mean(0)
 err=max(cKDTree(va).query(vb)[0].max(),cKDTree(vb).query(va)[0].max())
 print('SAVED',name,'shape error',err,'bounds',b.extents.tolist(),flush=True)
 out[name]={'max_vertex_error_mm':err,'bounds_size_mm':b.extents.tolist()}
adapted={}
for o in cfg.findall('object'):
 p={m.get('key'):m.get('value') for m in o.find('part').findall('metadata')}
 name=p['name'].replace('.stl','')
 off=np.array([float(p['source_offset_'+a]) for a in 'xyz'])
 tm=trimesh.load_mesh(ROOT/'output/Sanding-Block-Quarter-Sheet-A1-PETG/parts'/p['name'],process=False)
 adapted[name]=solid(tm).translate(off*S)
result={}
for name,moving,fixed,axis,center,phase in [('rear',adapted['Nut'],adapted['Tighteneer'],np.array([1.,0,0]),rear_center*S,202.5),('top',adapted['Screw'],adapted['Base'],top_axis,top_center*S,157.5)]:
 series=[]
 for angle in range(-720,721,15):
  v=(rotate_about(moving,phase+angle,axis,center).translate(axis*2*S*angle/360)^fixed).volume()
  series.append([angle,v])
 print('MOTION',name,'max',max(v[1] for v in series),'nonzero',[[a,v] for a,v in series if v>1e-6],flush=True)
 result[name]=series
(W/'r1-audit.json').write_text(json.dumps({'saved_mesh_comparison':out,'motion':result},indent=2))
