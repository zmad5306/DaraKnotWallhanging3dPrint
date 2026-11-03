from pathlib import Path
import json,sys,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];W=Path(__file__).resolve().parent
ns={'__file__':str(ROOT/'.work/sanding-block/finalize.py')}
exec((ROOT/'.work/sanding-block/finalize.py').read_text().split('path=OUT/')[0],ns)
source=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'output/Sanding-Block-Quarter-Sheet-A1-PLA-r3/Sanding-Block-Quarter-Sheet-A1-PLA-r3.3mf'
files=ns['load'](source);meshes=ns['read_geometry'](files)
fig,axes=plt.subplots(2,3,figsize=(14,8))
report={}
for ax,(name,m) in zip(axes.ravel(),meshes.items()):
    sec=m.section(plane_origin=[m.bounds[:,0].mean()+10,0,0],plane_normal=[1,0,0])
    if sec:
        for p in sec.discrete:ax.plot(p[:,1],p[:,2],color='navy',lw=1)
    ax.axhline(0,color='black');ax.set_aspect('equal');ax.set_title(name);ax.set_xlabel('bed Y (mm)');ax.set_ylabel('Z (mm)')
    facets=m.facets;areas=m.facets_area;normals=m.facets_normal
    ids=np.argsort(areas)[-8:][::-1]
    report[name]={'bounds':m.bounds.tolist(),'largest_faces':[{'area':float(areas[i]),'normal':normals[i].tolist(),'bounds':np.ptp(m.vertices[np.unique(m.faces[facets[i]])],axis=0).tolist()} for i in ids]}
axes[-1,-1].axis('off');fig.tight_layout();fig.savefig(W/'sections.png',dpi=160)
(W/'inspection.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in json.loads(files['Metadata/project_settings.config']).items() if 'support' in k or k in ['is_infill_first','wall_sequence','enable_overhang_speed']},indent=2))
