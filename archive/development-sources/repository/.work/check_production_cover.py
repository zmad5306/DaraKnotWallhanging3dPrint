import sys,json,zipfile,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
sys.path[:0]=['scripts','.work/python-libs']
import prepare_hammered_bands as b
from integrate_hammered_dara import selected_entries,plate_offset
from prepare_cover_precision_test import face_paths
prod=b.read_zip(Path('Dara.3mf'));test=b.read_zip(Path('Dara-Cover-Smooth-Crown-Test.3mf'))
pt=json.loads(Path('working/review/cover-crown-production/validation.json').read_text())['geometry_checks'][0]['build_transform'];pt=b.np.array(pt)
tt=b.np.array(json.loads(Path('.work/cover-crown/stage.json').read_text())['orientation']['build_transform'])
pm=selected_entries(prod,{'Band1'})['Band1'][0]['mesh'];tm=selected_entries(test,{'B1'})['B1'][0]['mesh']
world=pt.copy();world[:2,3]+=plate_offset(31,6)
pm.apply_transform(b.np.linalg.inv(world));tm.apply_transform(b.np.linalg.inv(tt))
err=max(b.cKDTree(pm.vertices).query(tm.vertices)[0].max(),b.cKDTree(tm.vertices).query(pm.vertices)[0].max())
print('Mesh counts',len(pm.faces),len(tm.faces),'max deviation mm',err)
for label,files in [('production',prod),('test',test)]:
 s=json.loads(files['Metadata/project_settings.config']);print(label,{k:s.get(k) for k in ['wall_generator','resolution','enable_arc_fitting']})
 cfg=ET.fromstring(files['Metadata/model_settings.config'])
 o=next(o for o in cfg.findall('object') if b.props(o)['name'].split(' - ')[0] in ['Band1','B1'])
 print(label,'overrides',b.props(o))
g=prod['Metadata/plate_31.gcode'].decode();Path('.work/cover-tessellation/production-plate31.gcode').write_text(g)
print('Object markers',[s for s in g.splitlines() if 'printing object' in s][:12])
print('sha',hashlib.sha256(Path('Dara.3mf').read_bytes()).hexdigest())
