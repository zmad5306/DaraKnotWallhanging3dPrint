# Historical design source retained for provenance, not a current rebuild command.
# Uses retired project paths/settings; do not regenerate current releases with it.
"""Production-derived screw-retained V1/V2 alignment guides for the A1.

Uses the accepted center r3 hardware stack without editing that release.
PYTHONPATH must include .work/python-libs and scripts.
"""
import argparse
import collections
import copy
import functools
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import shapely
from shapely import affinity, union_all
from shapely.geometry import Point, Polygon, box, shape, mapping
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import build_center_veneer_alignment_jig as j
from develop_m_veneer import prism
from mesh_sections import mesh_slice

ROOT = j.ROOT
REV = "r1"
OUT = ROOT/"output/Dara-Side-Veneer-Alignment-Jigs-A1"/REV
WORK = ROOT/".work/side-veneer-jig"/REV
EDIT = OUT/f"Dara-Side-Veneer-Alignment-Jigs-A1-{REV}-Editable.3mf"
FINAL = OUT/f"Dara-Side-Veneer-Alignment-Jigs-A1-{REV}.3mf"
OBJ_SETTINGS = dict(extruder="1",brim_width="1",enable_support="1")
BASE,GAP,WALL,TOP = j.BASE,j.GAP,j.WALL,j.GUIDE_TOP


def protected():
    result=j.protected()
    for p in sorted((j.PREVIOUS/"r3").glob("*")):
        if p.is_file():result[str(p.relative_to(ROOT))]=j.d.sha(p)
    result[str(Path(j.__file__).relative_to(ROOT))]=j.d.sha(Path(j.__file__))
    return result


@functools.lru_cache()
def extract():
    f=j.files(j.SOURCE)
    cfg=ET.fromstring(f["Metadata/model_settings.config"])
    root=ET.fromstring(f["3D/3dmodel.model"])
    plan=json.loads((j.PROD/"production-plan.json").read_text())
    poses=json.loads((j.PROD/"M-geometry-validation.json").read_text())
    offsets={"V1":[1584,-768],"V2":[0,-1152],"V3":[396,-1152]}
    meshes,records={},[]
    for co in cfg.findall("object"):
        name=j.d.props(co).get("name","")
        label=name.split()[0]
        if label not in ["C1","C2","C3","C4","C5","V1","V2","V3"]:continue
        entries,_=j.d.read_object(f,co.get("id"))
        m=entries[0]["mesh"]
        if label.startswith("V"):
            item=next(i for i in root.find(j.d.tag("build")) if i.get("objectid")==co.get("id"))
            T=j.d.transform(item.get("transform"))
            T[:2,3]-=offsets[label]
            m.apply_transform(T)
            m.apply_transform(np.linalg.inv(np.array(poses["skins"][int(label[1])-1]["assembly_to_printer"])))
        assert m.is_volume,label
        meshes[label]=m
        records.append(dict(name=name,object_id=co.get("id"),
                            mesh_sha256=hashlib.sha256(m.vertices.tobytes()+m.faces.tobytes()).hexdigest(),
                            removed_plate_offset_xy_mm=offsets.get(label)))
    regions=[shape(g) for g in plan["skin_regions"]]
    veneers,errors={},{}
    for i,region in enumerate(regions,1):
        actual=mesh_slice(meshes[f"V{i}"],9.5).intersection(region.buffer(.02))
        errors[f"V{i}"]=actual.symmetric_difference(region).area
        assert errors[f"V{i}"]<.02,(i,errors)
        veneers[f"V{i}"]=j.filled(actual)
    core=j.filled(union_all([mesh_slice(meshes[f"C{i}"],4) for i in range(1,6)]))
    return f,meshes,core,veneers,regions,records,errors,plan


def specs():
    return [
        dict(letter="L1",veneer="V1",name="L1 - left upper curve",core_name="C1",
             screw=(-262,71),window=box(-305,50,-200,91),
             tab=box(-307,63,-289,79),label=(-300,71),xy=(68,180)),
        dict(letter="L2",veneer="V1",name="L2 - left lower end",core_name="C4",
             screw=(-213,-170),window=box(-254,-190,-186,-135),
             tab=box(-228,-190,-202,-179),label=(-215,-185.2),xy=(55,86)),
        dict(letter="R1",veneer="V2",name="R1 - right upper curve",core_name="C2",
             screw=(213,148),window=box(160,119,251,171),
             tab=box(202,151,228,177),label=(215,171),xy=(179,180)),
        dict(letter="R2",veneer="V2",name="R2 - right lower end",core_name="C5",
             screw=(213,-148),window=box(105,-190,241,-130),
             tab=box(114,-190,140,-179),label=(126,-185.2),xy=(168,86),
             exclusion=Point(112.64025,-179.36775).buffer(2,quad_segs=24)),
    ]


def make_guides(core,veneers):
    pieces=[]
    for sp in specs():
        v=veneers[sp["veneer"]]
        foot=v.buffer(WALL+1,quad_segs=12).intersection(sp["window"]).union(sp["tab"])
        foot=foot.union(Point(sp["screw"]).buffer(8,quad_segs=24))
        assert foot.geom_type=="Polygon",sp["letter"]
        outside=core.buffer(GAP+WALL,quad_segs=12).intersection(
            v.buffer(GAP+WALL,quad_segs=12)).intersection(sp["window"])
        outside=outside.difference(sp.get("exclusion",Polygon()))
        def ring(clearance):
            return outside.difference(core.buffer(clearance,quad_segs=12).union(
                v.buffer(clearance,quad_segs=12)))
        normal,relief=ring(GAP),ring(.85)
        body=prism(foot,0,BASE)+prism(normal,BASE-.0001,BASE+8)
        body+=prism(relief,BASE+8-.0001,BASE+9.2)
        for z,c in [(9.2,.65),(9.4,.45),(9.6,.25),(9.8,GAP)]:
            body+=prism(ring(c),BASE+z-.0001,BASE+z+.2)
        body+=prism(normal,BASE+10-.0001,BASE+TOP)
        lettering=j.lettering(sp["letter"],sp["label"])
        assert lettering.difference(foot).area<1e-6
        assert lettering.intersection(core).area<1e-6,sp["letter"]
        body+=prism(lettering,BASE-.01,BASE+.4)
        shaft=Point(sp["screw"]).buffer(j.BORE/2,quad_segs=32)
        recess=Point(sp["screw"]).buffer(j.COUNTERBORE/2,quad_segs=32)
        body-=prism(shaft,-.1,BASE+.1)+prism(recess,-.1,j.RECESS)
        mesh=j.d.mesh(body)
        assert mesh.is_volume and len(body.decompose())==1,sp["letter"]
        pieces.append(dict(**sp,foot=foot,wall=normal,body=body,mesh=mesh,
                           shaft=shaft,recess=recess))
    return pieces


def build():
    OUT.mkdir(parents=True,exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)
    before=protected()
    f,mm,core,veneers,regions,sources,errors,plan=extract()
    ss=json.loads(j.files(j.COMPANION,False)["Metadata/project_settings.config"])
    for k,v in j.LOCKED.items():assert ss[k]==v,(k,ss[k])
    baseline=copy.deepcopy(ss)
    ss["print_settings_id"]=f"Dara side veneer alignment jigs {REV} - 8% gyroid"
    j.d.source=lambda:f
    j.d.source_path=lambda:j.SOURCE
    pieces=make_guides(core,veneers)
    cores=None
    for i in range(1,6):
        solid=j.d.solid(mm[f"C{i}"])
        cores=solid if cores is None else cores+solid
    visible=None
    for i,region in enumerate(regions,1):
        solid=j.d.solid(mm[f"V{i}"])^prism(region,8.6,13)
        visible=solid if visible is None else visible+solid
    entries,checks=[],[]
    placed=[]
    for sp in pieces:
        m,b=sp["mesh"],sp["body"]
        assert abs(m.bounds[0,2])<1e-6
        collision=abs((b^cores.translate([0,0,BASE])).volume())
        skin_collision=abs((b^visible.translate([0,0,BASE])).volume())
        assert max(collision,skin_collision)<1e-4,(sp["letter"],collision,skin_collision)
        support=sp["foot"].intersection(core).difference(sp["shaft"]).area
        assert support>350
        verts=mm[sp["veneer"]].vertices
        selected=shapely.contains_xy(sp["window"],verts[:,0],verts[:,1]) & (verts[:,2]>10.4)&(verts[:,2]<13)
        assert selected.any()
        front=float(verts[selected,2].min())
        assert front-TOP>.29,(sp["letter"],front)
        # No raised guide contacts the veneer joints or the center jig.
        seam_clearances=[]
        for row in plan["skin_seams"]:
            seam=shape(row["line"])
            seam_clearances.append(sp["wall"].distance(seam))
        assert min(seam_clearances)>10,(sp["letter"],seam_clearances)
        for row in plan["core_seams"]:
            assert sp["wall"].distance(shape(row["line"]))>10
        retention=j.check_retention(sp,mm)
        T=j.d.centered(m,xy=sp["xy"])
        entries.append(dict(name=sp["name"]+f" - {sp['veneer']} alignment {REV}",
                            parts=[dict(mesh=m,settings=dict(extruder="1"))],
                            transform=T,settings=copy.deepcopy(OBJ_SETTINGS)))
        bed_foot=affinity.translate(sp["foot"],*T[:2,3])
        assert box(3,3,253,253).covers(bed_foot.buffer(1.2))
        for previous in placed:assert bed_foot.distance(previous)>4
        placed.append(bed_foot)
        standalone=m.copy()
        standalone.apply_translation([-m.bounds[0,0],-m.bounds[0,1],0])
        stl=OUT/f"{sp['veneer']}-Jig-{REV}-{sp['letter']}.stl"
        standalone.export(stl)
        checks.append(dict(piece=sp["letter"],veneer=sp["veneer"],name=sp["name"],
                           source_window_xy_mm=list(sp["window"].bounds),size_mm=m.extents.tolist(),
                           stl_sha256=j.d.sha(stl),watertight=m.is_watertight,
                           connected_solids=len(b.decompose()),positive_volume=m.is_volume,
                           base_contact_area_mm2=sp["foot"].difference(sp["recess"]).area,
                           supported_core_area_mm2=support,core_intersection_mm3=collision,
                           all_veneers_intersection_mm3=skin_collision,
                           minimum_guide_clearance_below_front_mm=front-TOP,
                           veneer_seam_clearances_mm=seam_clearances,
                           screw_retention=retention,
                           tip_relief_radius_mm=2 if sp["letter"]=="R2" else None,
                           geometry=dict(foot=mapping(sp["foot"]),wall=mapping(sp["wall"]))))
    # Every side jig must coexist with the accepted center jig.
    center=j.shoes(core,veneers["V3"])
    coexistence=[]
    for sp in pieces:
        for cp in center:
            overlap=abs((sp["body"]^cp["body"]).volume())
            assert overlap<1e-5
            coexistence.append(dict(side=sp["letter"],center=cp["letter"],overlap_mm3=overlap))
    records=j.d.write_project(EDIT,[entries],ss["print_settings_id"],ss)
    assert protected()==before
    j.d.save_json(OUT/"geometry-validation.json",dict(
        revision=REV,purpose="Align V1 and V2 to assembled M using existing mounting screws; weights clamp",
        source_project=str(j.SOURCE),source_sha256=j.d.sha(j.SOURCE),
        source_objects=sources,source_section_z_mm=dict(core=4,veneer=9.5),
        actual_veneer_sections_vs_plan_area_error_mm2=errors,
        center_reference_project=str(j.FINAL),center_reference_sha256=j.d.sha(j.FINAL),
        profile_project=str(j.COMPANION),profile_sha256=j.d.sha(j.COMPANION),
        changed_variable="Add four shape-specific guides for V1/V2, retaining center r3 hardware stack and clearances",
        base_thickness_mm=BASE,clearance_per_side_mm=GAP,guide_top_above_core_back_mm=TOP,
        glue_relief=dict(assembly_z_mm=[8,9.2],setback_mm=.85,ramp_z_mm=[9.2,10]),
        pieces=checks,center_jig_coexistence=coexistence,placements=records,
        editable_sha256=j.d.sha(EDIT),locked_settings=j.LOCKED,
        intentional_object_settings=OBJ_SETTINGS,
        settings_changes={k:dict(old=baseline.get(k),new=v) for k,v in ss.items() if baseline.get(k)!=v},
        protected_files_before=before,protected_files_after=protected(),
        physical_fit_pending=True,physical_weight_load_not_qualified=True))
    draw(pieces,core,veneers,center)
    print("Built four side guides on one A1 plate:",EDIT,flush=True)


def poly(ax,g,**kw):
    for p in ([g] if g.geom_type=="Polygon" else g.geoms):
        if p.geom_type=="Polygon":ax.fill(*p.exterior.xy,**kw)


def draw(pieces,core,veneers,center):
    fig,axs=plt.subplots(1,3,figsize=(15,8),facecolor="#f5f3ef",
                         gridspec_kw=dict(width_ratios=[1,1,1.35]))
    colors={"V1":"#c28d54","V2":"#a77c5b"}
    for ax,vid in zip(axs[:2],["V1","V2"]):
        ax.set_facecolor("#f5f3ef")
        poly(ax,core,color="#d6d7d5")
        poly(ax,veneers[vid],color=colors[vid])
        for sp in pieces:
            if sp["veneer"]!=vid:continue
            poly(ax,sp["foot"],color="#439aaa",alpha=.8)
            poly(ax,sp["wall"],color="#144f59")
            ax.plot(*sp["screw"],"o",color="#152f37",markersize=5)
            ax.annotate(sp["letter"],sp["label"],xytext=(35 if vid=="V1" else -35,15),
                        textcoords="offset points",fontsize=13,weight="bold",
                        arrowprops=dict(arrowstyle="-",color="#144f59"))
        ax.set_xlim((-325,-90) if vid=="V1" else (90,325))
        ax.set_ylim(-205,200);ax.set_aspect("equal");ax.axis("off")
        ax.set_title(vid+" · "+("left" if vid=="V1" else "right"),fontsize=16)
    ax=axs[2];ax.set_facecolor("#f5f3ef")
    poly(ax,core,color="#d6d7d5")
    for sp in pieces:
        poly(ax,sp["foot"],color="#439aaa",alpha=.8)
        poly(ax,sp["wall"],color="#144f59")
        ax.plot(*sp["screw"],"o",color="#152f37",markersize=3)
    for cp in center:
        poly(ax,cp["foot"],color="#b2b9bb")
        poly(ax,cp["wall"],color="#778388")
    ax.set_aspect("equal");ax.axis("off")
    ax.set_title("All guides together\nCenter r3 shown in gray",fontsize=14)
    fig.suptitle(f"Side veneer alignment guides · A1 · {REV}",fontsize=23,weight="bold",color="#243b41")
    fig.text(.5,.07,"Black dots: existing mounting screws. Each guide attaches from underneath with a screw and 1 mm washer.",
             ha="center",fontsize=11)
    fig.text(.5,.035,"Same 10.4 mm base as center r3. Recessed heads leave the table flat; guide tops stay below the veneer face.",
             ha="center",fontsize=11)
    fig.subplots_adjust(top=.86,bottom=.14,left=.025,right=.98,wspace=.15)
    fig.savefig(OUT/f"Side-Jigs-{REV}-placement.png",dpi=150);plt.close(fig)
    # Native mesh views, with the same lettering as the actual parts.
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from matplotlib.colors import to_rgb
    fig=plt.figure(figsize=(13,9),facecolor="#f5f3ef")
    light=np.array([-.35,-.45,.82]);light/=np.linalg.norm(light)
    for i,sp in enumerate(pieces):
        ax=fig.add_subplot(2,2,i+1,projection="3d",facecolor="#f5f3ef")
        m=sp["mesh"].copy()
        m.apply_translation([-m.bounds[:,0].mean(),-m.bounds[:,1].mean(),0])
        colors=np.array(to_rgb("#439aaa"))[None,:]*(.55+.45*np.maximum(0,m.face_normals@light))[:,None]
        ax.add_collection3d(Poly3DCollection(m.triangles,facecolors=colors,edgecolors="none"))
        lo,hi=m.bounds
        ax.set_xlim(lo[0]-2,hi[0]+2);ax.set_ylim(lo[1]-2,hi[1]+2);ax.set_zlim(0,BASE+TOP)
        ax.set_box_aspect([m.extents[0],m.extents[1],BASE+TOP])
        ax.view_init(elev=45,azim=-65);ax.axis("off")
        ax.set_title(sp["name"],fontsize=14)
    fig.suptitle("Four printable guides · all screws enter from underneath",fontsize=20,weight="bold")
    fig.text(.5,.025,"Teal distinguishes the geometry here. All four objects print in white PLA.",ha="center")
    fig.subplots_adjust(top=.9,bottom=.07,left=.01,right=.99,hspace=.05)
    fig.savefig(OUT/f"Side-Jigs-{REV}-meshes.png",dpi=150);plt.close(fig)


def toolpath_checks(text,entries,proof):
    _,_,core,veneers,_,_,_,_=extract()
    fit_outline=core.union(union_all(list(veneers.values())))
    rows=list(j.extrusions(text))
    support_report,guide_report=[],[]
    fig,axs=plt.subplots(2,2,figsize=(9,9),facecolor="#f5f3ef")
    for ax,(name,row) in zip(axs.flat,entries.items()):
        label=name.split()[0]
        sp=next(x for x in proof["pieces"] if x["piece"]==label)
        T=row["T"];assert np.allclose(T[:3,:3],np.eye(3))
        m=row["parts"][0]["mesh"].copy();m.apply_transform(T)
        lo,hi=m.bounds
        bounds=box(lo[0]-.5,lo[1]-.5,hi[0]+.5,hi[1]+.5)
        local=[(z,g,f) for z,g,f in rows if g.intersects(bounds)]
        fit=affinity.translate(fit_outline,*T[:2,3])
        critical=[round(BASE+h,2) for h in [1.8,7.8,8.4,9.2,9.4,9.6,9.8,10,10.2]]
        beadrows={z:union_all([g for zz,g,f in local if zz==z and f not in ["Brim","Support","Support interface"]])
                  for z in critical}
        clearances,overhangs=[],[]
        for z,beads in beadrows.items():
            assert not beads.is_empty,(label,z)
            assert beads.intersection(fit).area<.0001,(label,z,"Fit collision")
            clearance=beads.distance(fit)
            assert clearance>.08,(label,z,clearance)
            clearances.append(dict(z_mm=z,bead_clearance_mm=clearance))
            if z>=round(BASE+9.4,2):
                below=mesh_slice(m,z-.3)
                distance=max(float(shapely.distance(shapely.points(shapely.get_coordinates(g)),below).max())
                             for g in ([beads] if beads.geom_type=="Polygon" else beads.geoms))
                assert distance<.29,(label,z,distance)
                overhangs.append(dict(z_mm=z,maximum_advance_mm=distance))
        guide_report.append(dict(piece=label,clearances=clearances,relief_ramp=overhangs))
        p=Point(np.array(sp["screw_retention"]["existing_pilot_xy_mm"])+T[:2,3])
        pocket=p.buffer(j.COUNTERBORE/2,quad_segs=32)
        supports=[(z,g,f) for z,g,f in local if f.startswith("Support") and g.intersects(pocket)]
        assert supports,(label,"No local support")
        heights=sorted(set(z for z,g,f in supports));top=max(heights)
        assert abs(j.RECESS-top-.2)<.02
        interface=union_all([g for z,g,f in supports if z==top])
        roof=union_all([g for z,g,f in local if abs(z-j.RECESS-.2)<.01
                        and not f.startswith("Support") and g.intersects(pocket)])
        bearing=p.buffer(5,quad_segs=32).difference(p.buffer(j.BORE/2+.1,quad_segs=32))
        coverage=roof.intersection(bearing).area/bearing.area
        assert coverage>.95,(label,coverage)
        gap=float(shapely.distance(shapely.points(shapely.get_coordinates(bearing)),interface).max())
        assert gap<1.,(label,gap)
        support_report.append(dict(piece=label,support_layer_top_z_mm=heights,
                                   roof_underside_z_mm=j.RECESS,support_gap_mm=j.RECESS-top,
                                   washer_seat_first_layer_coverage=coverage,
                                   maximum_bearing_boundary_gap_to_interface_mm=gap,
                                   actual_support_extrusions=len(supports)))
        for geom,color,alpha in [(pocket,"#eeeeea",1),(roof.intersection(pocket),"#76b5bc",.6),(interface,"#cf9149",.9)]:
            for g in ([geom] if geom.geom_type=="Polygon" else geom.geoms):
                if g.geom_type!="Polygon":continue
                ax.fill(*g.exterior.xy,color=color,alpha=alpha)
                for ring in g.interiors:ax.fill(*ring.xy,color="#f5f3ef")
        ax.set_aspect("equal");ax.axis("off");ax.set_title(label+" screw seat",fontsize=14)
    fig.suptitle("Actual A1 paths · roof in teal, support interface in gold",fontsize=16)
    fig.tight_layout()
    fig.savefig(OUT/f"Side-Jigs-{REV}-support-check.png",dpi=140);plt.close(fig)
    return dict(guides=guide_report,counterbore_supports=support_report)


def validate(folder,publish=True):
    proof=json.loads((OUT/"geometry-validation.json").read_text())
    assert proof["editable_sha256"]==j.d.sha(EDIT)
    assert proof["protected_files_before"]==protected()
    result=json.loads((folder/"result.json").read_text())
    assert result["return_code"]==0
    ef=j.files(EDIT);nf=j.files(folder/"sliced.3mf")
    es=json.loads(ef["Metadata/project_settings.config"])
    ns=json.loads(nf["Metadata/project_settings.config"])
    baseline=json.loads(j.files(j.COMPANION,False)["Metadata/project_settings.config"])
    assert es==ns,"Native save changed project settings"
    diff={k:dict(old=baseline.get(k),new=es.get(k)) for k in es.keys()|baseline.keys() if es.get(k)!=baseline.get(k)}
    assert set(diff)=={"print_settings_id"},diff
    for k,v in j.LOCKED.items():assert es[k]==v,(k,es.get(k))
    a,b=j.project_entries(ef),j.project_entries(nf)
    assert a.keys()==b.keys() and len(a)==4
    roundtrip,overrides=[],[]
    for name,row in a.items():
        saved=b[name]
        assert {k:v for k,v in row["settings"].items() if k is not None}=={k:v for k,v in saved["settings"].items() if k is not None}
        assert all(row["settings"][k]==v for k,v in OBJ_SETTINGS.items())
        for r,s in zip(row["parts"],saved["parts"]):
            for k in set(es)|{"extruder"}:
                assert r["settings"].get(k,row["settings"].get(k,es.get(k)))==s["settings"].get(k,saved["settings"].get(k,ns.get(k))),(name,k)
            for ob,part in [(row,r),(saved,s)]:
                for k,v in j.LOCKED.items():assert part["settings"].get(k,ob["settings"].get(k,es[k]))==v
        def vertices(r):
            vv=np.concatenate([x["mesh"].vertices for x in r["parts"]])
            return vv@r["T"][:3,:3].T+r["T"][:3,3]
        av,bv=vertices(row),vertices(saved)
        error=max(cKDTree(av).query(bv)[0].max(),cKDTree(bv).query(av)[0].max())
        assert error<.001,(name,error)
        roundtrip.append(dict(name=name,maximum_mesh_pose_error_mm=float(error)))
        overrides.append(dict(name=name,settings={k:v for k,v in saved["settings"].items() if k is not None},
                              effective_volume_settings_equal=True))
    with zipfile.ZipFile(folder/"sliced.3mf") as z:
        assert z.testzip() is None
        gnames=[n for n in z.namelist() if n.endswith(".gcode")]
        assert len(gnames)==1
        gb=z.read(gnames[0]);text=gb.decode()
        checksum=z.read(gnames[0]+".md5").decode().strip()
        assert hashlib.md5(gb).hexdigest().upper()==checksum.upper()
    config={}
    for line in text.splitlines():
        if line.startswith("; ") and " = " in line:
            k,v=line[2:].split(" = ",1);config[k]=v
    for k,v in j.LOCKED.items():
        assert config.get(k)==(";".join(v) if isinstance(v,list) else v),(k,config.get(k))
    scan=j.scan_gcode(text)
    assert scan["conservative_bed_edge_clearance_mm"]>2
    assert not scan["features"].get("Prime tower",0)
    assert scan["features"].get("Support",0)>0
    assert set(scan["model_extrusion_z_by_filament_mm"])=={"1"}
    assert "; EXECUTABLE_BLOCK_END" in text
    log=(folder/"slice.log").read_text(errors="replace")
    suspicious=[ln for ln in log.splitlines() if any(w in ln.lower() for w in ["floating","collision","non-manifold","empty layer"])]
    assert not suspicious,suspicious
    est=result["sliced_plates"][0]
    assert not est.get("warning_message"),est.get("warning_message")
    paths=toolpath_checks(text,a,proof)
    assert protected()==proof["protected_files_before"]
    report=dict(revision=REV,editable_sha256=j.d.sha(EDIT),native_sha256=j.d.sha(folder/"sliced.3mf"),
                generator_sha256=j.d.sha(Path(__file__)),center_helper_sha256=j.d.sha(Path(j.__file__)),
                native_return_code=0,slicer_result=result,locked_settings=j.LOCKED,
                full_project_settings_equal_editable=True,full_settings_changes_from_A1_companion=diff,
                all_effective_object_and_volume_settings_checked=overrides,mesh_roundtrip=roundtrip,
                gcode_sha256=hashlib.sha256(gb).hexdigest(),gcode_md5=checksum,
                gcode_configuration_checked=True,toolpaths=scan,actual_local_toolpath_checks=paths,
                suspicious_native_log_lines=suspicious,native_warning_message=est.get("warning_message",""),
                estimate_seconds=est["total_predication"],
                estimate_grams=sum(v["total_used_g"] for v in est["filaments"]),
                protected_files_after=protected(),physical_fit_pending=True)
    if publish:
        j.d.save_json(OUT/"native-validation.json",report)
        shutil.copyfile(folder/"sliced.3mf",FINAL)
    print("Validated:",folder,"Estimate:",report["estimate_seconds"],"s",report["estimate_grams"],"g",flush=True)
    return report


def native(reopen=False):
    folder=WORK/("reopen" if reopen else "native");folder.mkdir(parents=True,exist_ok=True)
    source=FINAL if reopen else EDIT
    original=j.d.sha(source)
    with (folder/"slice.log").open("w") as log:
        p=subprocess.run([str(j.EXE),"--slice","1","--export-3mf","sliced.3mf",
                          "--outputdir",str(folder),str(source)],cwd=j.EXE.parent,
                         stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    print("Native return:",p.returncode,flush=True)
    assert p.returncode==0
    report=validate(folder,publish=not reopen)
    assert original==j.d.sha(source)
    if reopen:
        current=json.loads((OUT/"native-validation.json").read_text())
        current["native_reopen_validation"]=dict(
            input_sha256=original,return_code=0,method="Reopen final project and reslice its A1 plate",
            warning_message=report["native_warning_message"],mesh_roundtrip=report["mesh_roundtrip"],
            full_project_and_effective_object_settings_checked=True,
            actual_local_toolpath_checks=report["actual_local_toolpath_checks"])
        j.d.save_json(OUT/"native-validation.json",current)
    shutil.copyfile(Path(__file__),OUT/f"build_side_veneer_alignment_jigs_{REV}.py")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=["build","slice","validate","reopen"])
    args=p.parse_args()
    if args.action=="build":build()
    elif args.action=="slice":native()
    elif args.action=="reopen":native(reopen=True)
    else:validate(WORK/"native")
