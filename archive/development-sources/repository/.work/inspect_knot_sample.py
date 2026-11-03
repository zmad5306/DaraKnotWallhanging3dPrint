import sys, json, xml.etree.ElementTree as E
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from integrate_hammered_dara import *
from build_jointed_bambu_project import read_array
from prepare_hammered_bands import trimesh, rotation
f=read_zip(ROOT/'Dara.3mf');r=E.fromstring(f['3D/3dmodel.model']);c=E.fromstring(f['Metadata/model_settings.config'])
entries=selected_entries(f,{'F4','F7'})
cad=(ROOT/'working/Dara-Photo-Frame-A1-Jointed.scad').read_text(); ps=read_array(cad,'frame_placements')
print('joint',read_array(cad,'frame_joints')[0])
for name,parts in entries.items():
 co=next(o for o in c.findall('object') if props(o)['name']==name)
 bi=next(i for i in r.find(tag('build')) if i.get('objectid')==co.get('id'))
 print(name,props(co),'build',bi.attrib)
 for p in parts: print(' part',props(p['config']),p['config'].attrib,p['mesh'].bounds.tolist(),p['mesh'].is_volume)
 stl=trimesh.load_mesh(ROOT/f'working/stl/Dara-Photo-Frame-A1-Jointed/{name}.stl')
 mesh=parts[0]['mesh'].copy(); mesh.apply_transform(np.linalg.inv(transform(bi.get('transform'))))
 print('stl bound',stl.bounds,'body local',mesh.bounds,'compare distance',cKDTree(stl.vertices).query(mesh.vertices)[0].max())
s=json.loads(f['Metadata/project_settings.config'])
print('settings',{k:v for k,v in s.items() if any(t in k for t in ['wipe_tower','prime','support','infill','shell_layers'])})
print('plate7',xml(c.findall('plate')[6]).decode())
print('gcode rels',f['Metadata/_rels/model_settings.config.rels'].decode()[:1000])
