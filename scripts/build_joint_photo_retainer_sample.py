"""Corrected r2: current J3 plus an identified photo-retainer blind-hole bolster.

The withdrawn r1 selected an M screw. Require the photo-anchor provenance,
3.175 mm blind bore, Z10.7 bore end, and unbroken Z13.5 show face here.
"""
import json
import math
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'.work/python-libs'),str(ROOT/'scripts')]
import numpy as np
import shapely
import manifold3d as mf
from shapely.geometry import Point,LineString
import build_joint_screw_bolster_sample as base
from remove_unused_project_filaments import read,write,dump,digest,EXE,props
from organize_root_projects import rows
from development_3mf import solid,mesh
from audit_knot_rollback_joints import paths_with_width,vertical_hits
from develop_cosmetic_joints import cross_section
from build_photo_support_test import paths as all_extrusions

base.NAME='Dara-A2L-Joint-Photo-Retainer-Bolster-r2'
base.TITLE='A2L J3 and photo-retainer bolster - 8% gyroid - r2'
base.OUT=ROOT/'output'/base.NAME
base.WORK=ROOT/'.work/joint-photo-retainer-bolster-r2'
base.EDIT=base.WORK/'editable.3mf'
base.FINAL=base.OUT/(base.NAME+'.3mf')
base.CROP=(-14.,-38.,66.,38.)
base.CENTERS=[[80.,110.],[205.,110.]]
base.NAMES=['A - J3 F2 tongue','B - J3 F3 socket and PHOTO RETAINER blind-hole bolster']
base.JOINT_INDEX=2
base.ALLOW_SOURCE_OPENINGS=True
base.REQUIRE_PHOTO_RETAINER=True
base.WITHDRAWN=False

def normalization_check():
    folder=base.WORK/'support-normalization-check';folder.mkdir(exist_ok=True)
    files=read(base.EDIT);s=json.loads(files['Metadata/project_settings.config'])
    assert s['independent_support_layer_height']=='1'
    s['independent_support_layer_height']='0';files['Metadata/project_settings.config']=json.dumps(s,indent=2).encode()
    source=folder/'diagnostic.3mf';write(source,files,base.EDIT)
    for attempt in range(3):
        with (folder/f'run-{attempt+1}.log').open('w') as log:
            p=subprocess.run([str(EXE),'--slice','0','--export-3mf','sliced.3mf','--outputdir',str(folder),str(source)],
                cwd=EXE.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        if p.returncode!=3221225477:break
    p.check_returncode();assert json.loads((folder/'result.json').read_text())['return_code']==0

def target_audit():
    """Inspect the native output before it can be promoted to the user file."""
    candidate=base.WORK/'native/sliced.3mf';settings,objects=rows(candidate)
    record=json.loads((base.OUT/'geometry-validation.json').read_text());identity=record['photo_retainer_identity']
    assert identity['role']=='PHOTO_RETAINER_BLIND_SCREW_HOLE' and identity['matches_M_mount'] is False
    obj=objects[1];bolsters=[p for p in obj['parts'] if p['settings'].get('name')=='Local solid screw reinforcement']
    assert len(bolsters)==1
    bolster=bolsters[0];center=bolster['mesh'].bounds[:,:2].mean(axis=0)
    plan=json.loads(base.PLAN.read_text());anchors=(np.array(plan['photo_anchors_mm'])+np.array(plan['photo_normals'])*9.5).reshape(-1,2)
    assert np.linalg.norm(anchors[identity['production_photo_anchor_flat_index']]-center)<.0001
    body=mf.Manifold.batch_boolean([solid(p['mesh']) for p in obj['parts'] if p['subtype']=='normal_part'],mf.OpType.Add)
    heights=vertical_hits(mesh(body),center);assert np.allclose(heights,[10.7,13.5],atol=.0001)
    assert Point(center).buffer(7).difference(cross_section(body,13.4)).area<.001
    assert np.allclose(bolster['mesh'].bounds[:,2],[0,12.4],atol=.0001)
    files=read(candidate);text=files['Metadata/plate_1.gcode'].decode()
    config=ET.fromstring(files['Metadata/model_settings.config'])
    labels={props(i)['object_id']:int(props(i)['identify_id']) for i in config.find('plate').findall('model_instance')}
    paths=paths_with_width(text,obj['transform'],labels[str(obj['id'])])
    _,production_objects=rows(base.SOURCE);production_object=production_objects[2]
    production_paths=paths_with_width(read(base.SOURCE)['Metadata/plate_3.gcode'].decode(),production_object['transform'])
    near=[p for p in paths if LineString(p[2][:,:2]).distance(Point(center))<.9]
    first=min(p[2][1,2] for p in near)
    assert 10.79<=first<=11.01,(first,'Native blind hole depth does not match production')
    assert not any(p[2][1,2]<10.79 for p in near)
    tr=obj['transform'];bed=(np.array([*center,0])@tr[:3,:3].T+tr[:3,3])[:2]
    bore_support=[p for p in all_extrusions(text) if p['feature'] in ('Support','Support interface','Support transition')
        and LineString(p['segment']).distance(Point(bed))<1.3]
    roi=Point(center).buffer(7);skin=[]
    for z in [12.8,13,13.2,13.4,13.6]:
        ps=[p for p in paths if abs(p[2][1,2]-z)<.001 and LineString(p[2][:,:2]).distance(roi)<1]
        assert ps and not any(p[1]=='Sparse infill' for p in ps)
        bands=shapely.union_all([LineString(p[2][:,:2]).buffer(p[3]/2,quad_segs=8) for p in ps])
        fraction=bands.intersection(roi).area/roi.area
        reference=[p for p in production_paths if abs(p[2][1,2]-z)<.001 and LineString(p[2][:,:2]).distance(roi)<1]
        reference_bands=shapely.union_all([LineString(p[2][:,:2]).buffer(p[3]/2,quad_segs=8) for p in reference])
        baseline=reference_bands.intersection(roi).area/roi.area
        if z==12.8:
            # Preserve the production bridge line spacing instead of imposing
            # a solid-fill coverage threshold on a bridge over sparse infill.
            assert any(p[1]=='Bridge' for p in ps) and any(p[1]=='Bridge' for p in reference)
        else:assert fraction>.98,(z,fraction)
        assert abs(fraction-baseline)<.005,(z,fraction,baseline)
        skin.append(dict(z_mm=z,commanded_coverage_fraction=fraction,production_coverage_fraction=baseline,
            features=sorted(set(p[1] for p in ps))))
    proof=dict(native_project_sha256=digest(candidate),feature='PHOTO_RETAINER_BLIND_SCREW_HOLE',
        center_assembly_mm=center.tolist(),production_photo_anchor_flat_index=identity['production_photo_anchor_flat_index'],
        native_mesh_center_z_hits_mm=heights,first_native_model_extrusion_over_bore_mm=float(first),
        bore_open_from_back=True,show_face_unbroken_over_full_14mm_bolster=True,
        support_extrusions_within_retainer_bore_radius_1_3mm=len(bore_support),
        retainer_bore_support_cleanup_required=bool(bore_support),
        screw_modifier_z_mm=[0,12.4],skin_layers=skin,actual_geometry_and_gcode_checked=True)
    dump(base.OUT/'photo-retainer-audit.json',proof)
    print('Verified the native sample contains the photo-retainer blind bore, solid exposed face and capped reinforcement.',flush=True)

def document(report,record):
    mins=round(report['estimated_seconds']/60);ident=record['photo_retainer_identity'];c=record['bolsters'][0]['center_assembly_mm']
    text=f'''# Current photo-retainer bolster + joint test — r2

**Use `{base.FINAL.name}`.** A2L / 0.4 mm nozzle / Textured PEI. One plate with both mating pieces. Open as a Bambu Studio **project**. Estimate: **{mins//60}h {mins%60:02d}m / {report['estimated_grams']:.2f} g** including supports and purge tower.

**r1 is withdrawn because it selected an M mounting through-hole reinforcement.** Its previous digital checks did not establish that it contained the requested photo-retainer feature. This r2 replaces it for the user's test.

- **A / left:** current production J3, F2 tongue, both locating keys.
- **B / right:** current production J3, F3 socket, both grooves and the complete **photo-retainer screw bolster beneath the exposed face**.
- The retainer has a **3.175 mm blind hole from the back ending at Z10.7**, with uninterrupted material up to the **Z13.5 show face**. Its **14 mm diameter / 100% infill** reinforcement modifier ends at **Z12.4**, leaving the saved five top layers above it. This is not an M through hole.

The matching modifier center is assembly XY ({c[0]:.6f}, {c[1]:.6f}) mm, matched to production photo-anchor index {ident['production_photo_anchor_flat_index']} (zero-based flattened index). The native mesh and actual G-code are checked for the blind bore and covered face; the generic modifier name alone is not accepted as identification.

## Print and inspect

1. Use the saved A2L project and its original three slots: **1 white, 2 wood tan, 3 Azurite blue**.
2. Remove the normal supports from both joint grooves. Dry-fit both keys before gluing or sanding and check that the visible faces meet flush. Normal support material also fills the retainer blind hole; clear it from the back if testing the screw. Support removal remains physically unqualified.
3. Inspect the unbroken show face directly opposite the photo-retainer blind hole for the unwanted circular mark. `feature-guide.png` locates that region on the assembled sample.

**Infill-first is OFF; supports are normal(auto).** Structural 8% gyroid, 0.20 mm initial/regular layers, four walls, five top/bottom layers, 0.20 mm support top gap and interface spacing, material profiles, finish directions and original rotations remain. The screw modifier alone retains 100% infill. No production file is changed and no printer job is sent. Digital checks do not establish physical fit, cleanup or surface appearance.

## Exact source and changes

- Source: current `Knot.3mf`, SHA-256 `{base.SOURCE_SHA}`.
- Sample SHA-256: `{report['sample_sha256']}`.
- Full-scale J3 crop: joint-local **X −14 to +66 mm, Y −38 to +38 mm**, Z −0.01 to 20 mm. Envelope 80 × 76 × 13.5 mm.
- Crop only; joint dimensions, both complete keys, blind screw hole, photo opening, material boundaries and complete reinforcement are unchanged. The edge reliefs are portions of the actual production photo openings, verified against the source, not new recesses. Both pieces remain connected.
- Translation-only placement, sample label and single-plate tower arrays are the only packaging differences. Tower X285 / Y160. No M mounting through-hole reinforcement is included.

`geometry-validation.json` records source comparisons and semantic photo-retainer identification. `photo-retainer-audit.json` separately checks that exact feature in the native mesh and toolpaths. `validation.json` records the settings, joint clearances, support backing, five top layers, native reopen, checksums, estimates and protected-file hashes.

Bambu's sample G-code footer retains independent support layer height 1 while production records its normalized value 0. The editable setting remains 1 in both projects. A diagnostic slice using 0 is required to produce identical printer commands before release; the delivered project preserves production's saved setting.
'''
    staged=base.WORK/'README.pending';staged.write_text(text,encoding='utf-8',newline='\n');staged.replace(base.OUT/'README.md')

base.document=document

def guide():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from audit_knot_rollback_joints import local
    _,objects=rows(base.FINAL)
    record=json.loads((base.OUT/'geometry-validation.json').read_text());j=record['source_joint_record']
    c=np.array(record['bolsters'][0]['center_assembly_mm']);q=local(Point(c),j)
    bodies=[mf.Manifold.batch_boolean([solid(p['mesh']) for p in o['parts'] if p['subtype']=='normal_part'],mf.OpType.Add) for o in objects]
    fig,axes=plt.subplots(1,3,figsize=(14,5),gridspec_kw={'width_ratios':[1,1,.95]})
    for ax,z,title in zip(axes[:2],[13.4,.1],['Front: inspect the exposed face','Back: locate the blind screw hole']):
        for i,body in enumerate(bodies):
            shape=local(cross_section(body,z),j)
            for p in getattr(shape,'geoms',[shape]):
                ax.fill(*p.exterior.xy,color=['#cedce5','#e5dfd4'][i],edgecolor='none')
                for h in p.interiors:ax.fill(*h.xy,color='white')
        ax.add_patch(plt.Circle((q.x,q.y),7,fill=False,edgecolor='#bf302a',lw=2))
        if z<1:ax.add_patch(plt.Circle((q.x,q.y),3.175/2,facecolor='white',edgecolor='#bf302a',lw=1))
        ax.annotate('PHOTO RETAINER',xy=(q.x,q.y+7),xytext=(38,43),fontsize=9,ha='center',color='#a5221d',
            arrowprops={'arrowstyle':'->','color':'#a5221d'})
        ax.text(-8,-43,'A / F2',ha='center',fontsize=9);ax.text(39,-43,'B / F3',ha='center',fontsize=9)
        ax.set_xlim(-18,70);ax.set_ylim(-47,49);ax.set_aspect('equal');ax.axis('off');ax.set_title(title,fontsize=11)
    ax=axes[2];body=mesh(bodies[1]);angle=math.radians(j[3]);direction=np.array([math.cos(angle),math.sin(angle)])
    positions=np.linspace(-8,8,801);bottom=[];top=[]
    for x in positions:
        heights=vertical_hits(body,c+x*direction);assert len(heights)==2
        bottom.append(heights[0]);top.append(heights[1])
    bottom=np.array(bottom);top=np.array(top)
    ax.fill_between(positions,bottom,top,color='#e5dfd4',edgecolor='none')
    mask=abs(positions)<=7
    ax.fill_between(positions[mask],bottom[mask],12.4,color='#dba257',alpha=.9)
    ax.plot(positions,bottom,color='#444444',lw=1);ax.plot(positions,top,color='#444444',lw=1)
    ax.hlines(12.4,-7,7,color='#bf302a',ls='--',lw=1.5)
    ax.annotate('Exposed face: 13.5 mm',xy=(0,13.5),xytext=(0,16),ha='center',fontsize=9,arrowprops={'arrowstyle':'->'})
    ax.annotate('Bolster ends: 12.4 mm',xy=(5,12.4),xytext=(0,18),ha='center',fontsize=9,color='#a5221d',arrowprops={'arrowstyle':'->','color':'#a5221d'})
    ax.text(0,6,'BLIND HOLE\n3.175 mm\nends at Z10.7',ha='center',fontsize=8,bbox={'facecolor':'white','alpha':.9,'edgecolor':'none'})
    ax.set_xlim(-9,9);ax.set_ylim(0,19);ax.set_xlabel('Distance from screw centre (mm)');ax.set_ylabel('Height from back (mm)');ax.set_title('Section through the actual retainer hole',fontsize=11);ax.grid(alpha=.15)
    fig.suptitle('r2 — Joint with the photo-retainer bolster',fontsize=15)
    fig.text(.5,.015,'Assembly positions shown. Diagram shading identifies the pieces and hidden reinforcement; production filament colors are unchanged.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.06,1,.92]);fig.savefig(base.OUT/'feature-guide.png',dpi=170);plt.close(fig)

if __name__=='__main__':
    action=sys.argv[1]
    if action=='build':base.build()
    elif action=='slice':base.native();normalization_check()
    elif action=='validate':target_audit();base.validate();guide()
    elif action=='guide':guide()
    elif action=='docs':document(json.loads((base.OUT/'validation.json').read_text()),json.loads((base.OUT/'geometry-validation.json').read_text()))
    else:raise ValueError(action)
