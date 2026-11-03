import sys,json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'.work/python-libs'),str(ROOT/'scripts')]
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import shape,Polygon
from shapely import union_all
from development_3mf import read_object,props,transform,tag,save_json,sha
from mesh_sections import mesh_slice
W=ROOT/'.work/center-veneer-jig';W.mkdir(exist_ok=True)
with zipfile.ZipFile(ROOT/'Dara.3mf') as z:
    f={n:z.read(n) for n in z.namelist() if n in ['3D/3dmodel.model','Metadata/model_settings.config'] or n.startswith('3D/Objects/')}
cfg=ET.fromstring(f['Metadata/model_settings.config'])
r=ET.fromstring(f['3D/3dmodel.model'])
p=json.loads((ROOT/'working/bambu/Dara-Photo-Frame-A2L/production-plan.json').read_text())
report=json.loads((ROOT/'working/bambu/Dara-Photo-Frame-A2L/M-geometry-validation.json').read_text())
meshes={}
for co in cfg.findall('object'):
    name=props(co).get('name','')
    if not name.startswith(('C1 ','C2 ','C3 ','C4 ','C5 ','V3 ')):continue
    parts,st=read_object(f,co.get('id'))
    m=parts[0]['mesh']
    if name.startswith('V3 '):
        item=next(it for it in r.find(tag('build')) if it.get('objectid')==co.get('id'))
        T=transform(item.get('transform'));T[:2,3]-=[396,-1152]
        m.apply_transform(T)
        m.apply_transform(np.linalg.inv(np.array(report['skins'][2]['assembly_to_printer'])))
    label=name.split()[0];meshes[label]=m
    np.savez_compressed(W/(label+'.npz'),vertices=m.vertices,faces=m.faces)
    print(label,co.get('id'),m.bounds.tolist(),m.is_volume)
v=mesh_slice(meshes['V3'],9.5)
expected=shape(p['skin_regions'][2])
v=v.intersection(expected.buffer(.02))
print('V3 section difference area',v.symmetric_difference(expected).area)
fig,axs=plt.subplots(1,2,figsize=(12,8))
colors=['#90a9bb','#c1d5df','#8ea09b','#d2d1c6','#d2c3b5']
for k,ax in enumerate(axs):
    for i in range(5):
        g=mesh_slice(meshes[f'C{i+1}'],4)
        for a in [g] if g.geom_type=='Polygon' else g.geoms:
            x,y=a.exterior.xy;ax.fill(x,y,color=colors[i],alpha=.7);ax.plot(x,y,color='#555',linewidth=.7)
        if k==0:
            c=g.representative_point();ax.text(c.x,c.y,f'C{i+1}')
    x,y=expected.exterior.xy;ax.plot(x,y,color='#9e4126',linewidth=2)
    for a in report['skins'][2]['anchors']:
        ax.plot(*a['xy_mm'],'ro',markersize=4)
    ax.set_aspect('equal');ax.grid(alpha=.2)
    if k:ax.set_xlim(-145,145)
axs[0].set_title('Assembled cores / center veneer in rust')
axs[1].set_title('Center veneer and existing locators')
fig.tight_layout();fig.savefig(W/'source-layout.png',dpi=150)
save_json(W/'source.json',dict(source_sha256=sha(ROOT/'Dara.3mf'),veneer_section_plan_error_mm2=v.symmetric_difference(expected).area))
