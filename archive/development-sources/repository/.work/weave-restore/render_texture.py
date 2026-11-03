import sys,zipfile,xml.etree.ElementTree as E
from pathlib import Path
sys.path.insert(0,"scripts")
from build_jointed_bambu_project import tag,P
from colorize_print_project import read_mesh
from validate_print_project import transform,props
import numpy as np,trimesh,matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
z=zipfile.ZipFile(".work/weave-restore/baseline.3mf");cfg=E.fromstring(z.read("Metadata/model_settings.config"));root=E.fromstring(z.read("3D/3dmodel.model"))
o=next(o for o in cfg.findall("object") if props(o)["name"]=="Test-Weave-Full-Width");pid=o.find("part[@subtype='normal_part']").get("id");c=next(c for c in root.find(tag("resources")).find(f"{tag('object')}[@id='{o.get('id')}']").find(tag("components")) if c.get("objectid")==pid);child=E.fromstring(z.read(c.get("{"+P+"}path").lstrip("/")));old=read_mesh(child.find(tag("resources")).find(f"{tag('object')}[@id='{pid}']"));old.apply_transform(transform(c.get("transform")))
new=trimesh.load_mesh("working/stl/Dara-Print-Checks/Test-Weave-Full-Width.stl")
fig=plt.figure(figsize=(10,5),facecolor="#f3f1ed")
for i,(m,title) in enumerate([(old,"Previous flat grid"),(new,"Restored over / under crossings")],1):
 select=(m.triangles[:,:,2].min(axis=1)>8.999)&(m.triangles[:,:,2].max(axis=1)<9.901)&(m.face_normals[:,2]>=-.001)
 tri=m.triangles[select];norms=m.face_normals[select]
 ax=fig.add_subplot(1,2,i,projection="3d");ax.set_facecolor("#f3f1ed")
 shade=.55+.45*np.clip(norms@np.array([-.32,-.38,.87]),0,1)
 ax.add_collection3d(Poly3DCollection(tri,facecolors=np.tile([.76,.63,.44],(len(tri),1))*shade[:,None],linewidths=0,edgecolors="none",antialiaseds=False))
 ax.set_xlim(-15,15);ax.set_ylim(-12,12);ax.set_zlim(9,10);ax.set_box_aspect((30,24,1));ax.view_init(elev=55,azim=-63);ax.set_axis_off();ax.set_title(title,fontsize=13,pad=-5)
fig.subplots_adjust(wspace=-.05,top=.92,bottom=.05,left=0,right=1)
fig.text(.5,.035,"Actual fabric surface geometry; crossing relief is 0.3 mm",ha="center",fontsize=10,color="#555555")
fig.savefig("working/review/weave-restoration/texture-comparison.png",dpi=150)
