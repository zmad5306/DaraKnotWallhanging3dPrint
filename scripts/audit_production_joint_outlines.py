"""Check all 14 saved production joints against the continuous artwork.

The check concerns the side scallops visible in the sample's top outline.
It does not qualify lap seating, supported undersides or physical strength.
"""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.work/python-libs'))
import numpy as np
import manifold3d as mf
from shapely import affinity,union_all
from shapely.geometry import box,Point
from development_3mf import solid,save_json,sha
from develop_cosmetic_joints import cross_section
from develop_m_veneer import locate
from add_blue_ribbon_edge import artwork
from extract_production_joint_sample import source_rows,protected

OUT=ROOT/'working/review/production-side-notches'


def run():
    baseline=protected()
    rows,_=source_rows([f'F{i} A2L knot' for i in range(1,11)])
    bodies=[mf.Manifold.batch_boolean([solid(p['mesh']) for p in row['parts'] if p['subtype']=='normal_part'],mf.OpType.Add) for row in rows]
    plan_path=ROOT/'working/bambu/Dara-Photo-Frame-A2L/production-plan.json'
    cad_path=ROOT/'working/Dara-Photo-Frame-A1-Jointed.scad'
    plan=json.loads(plan_path.read_text());cad=cad_path.read_text()
    K=artwork(cad,'knot_outline');F=artwork(cad,'fabric_outline').buffer(.1125,join_style=2)
    actual={z:union_all([cross_section(b,z) for b in bodies]) for z in [8.5,13.4]}
    pivots=(np.array(plan['photo_anchors_mm'])+np.array(plan['photo_normals'])*9.5).reshape(-1,2)
    upper_holes=union_all([Point(xy).buffer(2.02,quad_segs=32) for ci,fi,xy in plan['screw_mounts']])
    lower_holes=union_all([Point(xy).buffer(6.02,quad_segs=32) for ci,fi,xy in plan['screw_mounts']]
        +[Point(xy).buffer(1.61,quad_segs=32) for xy in pivots]
        +[Point(np.array(w[1])+[x,w[4]]).buffer(1.61,quad_segs=32) for w in plan['wall_mounts'] for x in w[5]])
    expected={13.4:K.difference(upper_holes),8.5:K.union(F).difference(lower_holes)}
    reports=[]
    for i,j in enumerate(plan['frame_joints']):
        zone=locate(box(-24,-j[4]/2-8,42,j[4]/2+8),j);checks=[]
        for z in [8.5,13.4]:
            a=actual[z].intersection(zone);e=expected[z].intersection(zone)
            missing=e.buffer(-.02).difference(a.buffer(.005))
            excess=a.difference((K if z>10 else K.union(F)).buffer(.02))
            assert missing.area<1e-6 and excess.area<1e-6,(i+1,z,missing.area,excess.area)
            checks.append(dict(z_mm=z,missing_beyond_0_025mm_tolerance_mm2=missing.area,
                               extra_outside_artwork_tolerance_mm2=excess.area))
        reports.append(dict(joint=i+1,parts=[j[0]+1,j[1]+1],checks=checks))
    OUT.mkdir(parents=True,exist_ok=True)
    plot(actual,plan['frame_joints'][3])
    assert protected()==baseline
    save_json(OUT/'outline-audit.json',dict(status='PASS_ALL_14_PRODUCTION_JOINT_OUTLINES',
        source_sha256=sha(ROOT/'Dara.3mf'),source_cad_sha256=sha(cad_path),plan_sha256=sha(plan_path),
        checker_sha256=sha(Path(__file__)),checks=reports,tolerance_mm=.025,
        comparison='Actual saved production cross-sections versus continuous artwork; existing hardware openings excluded.',
        finding='Sample crop intersected rounded adjacent openings in the knot outline. No extra production outline cutouts found.',
        scope='Visible outline at Z8.5 and Z13.4, not hidden lap clearance or physical fit.',
        production_and_A1_unchanged=True,protected_project_sha256=baseline))
    print('PASS: all 14 saved production joint outlines match continuous artwork; no production changes.',flush=True)


def plot(actual,j):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as Patch,Rectangle
    def local(g):return affinity.rotate(affinity.translate(g,-j[2][0],-j[2][1]),-j[3],origin=(0,0))
    full=local(actual[8.5]);white=local(actual[13.4])
    old=box(-24,-j[4]/2-1,42,j[4]/2+1);new=box(-24,-j[4]/2,42,j[4]/2)
    fig,axs=plt.subplots(1,3,figsize=(15,7))
    titles=['Full production: adjacent rounded openings','Old sample: crop crosses those corners','Corrected sample: straight cut boundaries']
    for i,(ax,title) in enumerate(zip(axs,titles)):
        mask=box(-45,-65,65,65) if i==0 else [old,new][i-1]
        for g,color in [(full.intersection(mask),'#b99c73'),(white.intersection(mask),'#d4dce1')]:
            polys=[g] if g.geom_type=='Polygon' else g.geoms
            for p in polys:
                if p.geom_type!='Polygon':continue
                ax.add_patch(Patch(np.array(p.exterior.coords),facecolor=color,edgecolor='#34434a',linewidth=.6))
                for ring in p.interiors:ax.add_patch(Patch(np.array(ring.coords),facecolor='white',edgecolor='#34434a',linewidth=.6))
        if i==0:
            ax.add_patch(Rectangle((-24,-j[4]/2-1),66,j[4]+2,fill=False,edgecolor='#8d3cb0',linestyle='--',linewidth=1.8))
            ax.text(8,-46,'Purple box = old sample crop',color='#743291',ha='center',fontsize=9)
            ax.set(xlim=(-45,65),ylim=(-65,65))
        else:
            ax.set(xlim=(-28,46),ylim=(-40,40))
            if i==1:
                for sign in [-1,1]:ax.annotate('',xy=(17,sign*34.1),xytext=(33,sign*38),arrowprops=dict(arrowstyle='->',color='#8d3cb0',lw=2))
        ax.set_title(title,fontsize=10);ax.set_aspect('equal');ax.set_xlabel('Along joint (mm)');ax.set_ylabel('Across ribbon (mm)')
    fig.suptitle('J4 — actual saved production geometry; only the sample crop changes',fontsize=14)
    fig.tight_layout();fig.savefig(OUT/'crop-comparison.png',dpi=170);plt.close(fig)


if __name__=='__main__':run()
