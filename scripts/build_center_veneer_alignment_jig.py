# Historical design source retained for provenance, not a current rebuild command.
# Uses retired project paths/settings; do not regenerate current releases with it.
"""Screw-retained V-crotch and bottom guides for saved production V3, r3.

Reads production meshes; never regenerates or edits M/knot/companion projects.
Run with the repository's .work/python-libs on PYTHONPATH.
"""
import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import shapely
from shapely.geometry import Polygon, LineString, Point, box, shape, mapping
from shapely import union_all
from scipy.spatial import cKDTree
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

import development_3mf as d
from develop_m_veneer import prism
from mesh_sections import mesh_slice
from validate_print_project import scan_gcode, TOKEN

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Dara.3mf"
COMPANION = ROOT / "working/bambu/Dara-A1-Companion/Dara-A1-Companion.3mf"
PROD = ROOT / "working/bambu/Dara-Photo-Frame-A2L"
REV = "r3"
PREVIOUS = ROOT / "output/Dara-Center-Veneer-Alignment-Jig-A1"
OUT = PREVIOUS / REV
WORK = ROOT / ".work/center-veneer-jig" / REV
EDIT = OUT / f"Dara-Center-Veneer-Alignment-Jig-A1-{REV}-Editable.3mf"
FINAL = OUT / f"Dara-Center-Veneer-Alignment-Jig-A1-{REV}.3mf"
EXE = Path(r"C:\Program Files\Bambu Studio\bambu-studio.exe")
BASE = 10.4
BORE = 4.4
COUNTERBORE = 12.
RECESS = 4.
SCREW_LENGTH = 12.7
WASHER_THICKNESS = 1.
HEAD_HEIGHT = 2.5
GAP = .15
WALL = 3.2
GUIDE_TOP = 10.2  # assembly Z; below the veneer edge at 10.5
LOCKED = dict(
    printer_model="Bambu Lab A1", nozzle_diameter=["0.4"],
    sparse_infill_density="8%", sparse_infill_pattern="gyroid",
    layer_height="0.2", initial_layer_print_height="0.2",
    wall_loops="4", top_shell_layers="5", bottom_shell_layers="5",
    curr_bed_type="Textured PEI Plate",
)


def files(path, geometry=True):
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist()
                if n in ["3D/3dmodel.model", "Metadata/model_settings.config",
                         "Metadata/project_settings.config", "[Content_Types].xml"]
                or (geometry and n.startswith("3D/Objects/"))}


def protected():
    paths = [SOURCE, PROD/"Dara-A2L-Complete.3mf", PROD/"Dara-A2L-Editable.3mf",
             PROD/"production-plan.json", PROD/"M-geometry-validation.json"]
    paths += sorted(COMPANION.parent.glob("*"))
    # Do not silently replace a file the user may already be printing.
    paths += sorted(PREVIOUS.glob("*r1*.3mf"))
    paths += sorted(PREVIOUS.glob("*r1*.stl"))
    paths += sorted((PREVIOUS/"r2").glob("*.3mf"))
    paths += sorted((PREVIOUS/"r2").glob("*.stl"))
    return {str(p.relative_to(ROOT)): d.sha(p) for p in paths if p.is_file()}


def filled(g):
    return union_all([Polygon(p.exterior) for p in
                      ([g] if g.geom_type == "Polygon" else g.geoms)
                      if p.geom_type == "Polygon"])


def extract():
    f = files(SOURCE)
    cfg = ET.fromstring(f["Metadata/model_settings.config"])
    root = ET.fromstring(f["3D/3dmodel.model"])
    plan = json.loads((PROD/"production-plan.json").read_text())
    poses = json.loads((PROD/"M-geometry-validation.json").read_text())
    meshes, records = {}, []
    for co in cfg.findall("object"):
        name = d.props(co).get("name", "")
        if not name.startswith(("C1 ", "C2 ", "C3 ", "C4 ", "C5 ", "V3 ")):
            continue
        entries, st = d.read_object(f, co.get("id"))
        m = entries[0]["mesh"]
        if name.startswith("V3 "):
            # Native save centers the carried mesh, then places it on plate 17.
            item = next(i for i in root.find(d.tag("build"))
                        if i.get("objectid") == co.get("id"))
            T = d.transform(item.get("transform"))
            T[:2, 3] -= [396, -1152]
            m.apply_transform(T)
            m.apply_transform(np.linalg.inv(np.array(poses["skins"][2]["assembly_to_printer"])))
        label = name.split()[0]
        assert m.is_volume, label
        meshes[label] = m
        records.append(dict(name=name, object_id=co.get("id"),
                            source_mesh_sha256=hashlib.sha256(
                                m.vertices.tobytes()+m.faces.tobytes()).hexdigest()))
    region = shape(plan["skin_regions"][2])
    # At Z9.5 all rear carrier stock and pockets have ended locally. Limit the
    # cross section to the verified V3 region to discard the remote bed guard.
    veneer = mesh_slice(meshes["V3"], 9.5).intersection(region.buffer(.02))
    error = veneer.symmetric_difference(region).area
    assert error < .01, error
    cores = union_all([mesh_slice(meshes[f"C{i}"], 4) for i in range(1, 6)])
    return f, meshes, filled(cores), filled(veneer), region, records, error


def lettering(text, xy):
    path = TextPath((0, 0), text, size=5.5,
                    prop=FontProperties(family="DejaVu Sans", weight="bold"))
    g = Polygon()
    for ring in path.to_polygons():
        g = g.symmetric_difference(Polygon(ring))
    from shapely import affinity
    b = g.bounds
    return affinity.translate(g, xy[0]-(b[0]+b[2])/2,
                              xy[1]-(b[1]+b[3])/2)


def shoes(core, veneer):
    # Flanks of the common V are the primary datum. The sharp apex and the
    # nearby core seam are deliberately relieved; neither is a hard stop.
    contour=veneer.boundary.intersection(box(-38,118,28,170))
    coords=shapely.get_coordinates(contour)
    apex=coords[np.argmin(coords[:,1])]
    plan=json.loads((PROD/"production-plan.json").read_text())
    seam=shape(plan["core_seams"][0]["line"])
    seam_end=Point(seam.coords[-1])
    exclusion=Point(apex).buffer(2,quad_segs=24).union(
        seam_end.buffer(3,quad_segs=24))
    specs = [
        dict(name="V - crotch datum", letter="V",
             window=box(-38,118,28,170), tab=box(-38,118,28,168),
             label=(-5,161), xy=(70,105), exclusion=exclusion,
             screw=(-30.064286999999997,108.08241498485857),
             anchor=(-30.064286999999997,126), core_name="C1",
             apex=apex.tolist(), seam_end=list(seam.coords[-1])),
        dict(name="B - stem bottom", letter="B",
             window=box(-48, -191, 37, -155), tab=box(-17, -190, 7, -179),
             label=(-5, -185.6), xy=(170,128),
             screw=(-29,-62), anchor=(-29,-165), core_name="C3"),
    ]
    result = []
    for sp in specs:
        win = sp["window"]
        # The compact V foot extends beneath the core. Its raised flanks
        # occupy the open crotch; the matching upper faces guide the veneer.
        foot = veneer.buffer(WALL+1.0, quad_segs=12).intersection(win).union(sp["tab"])
        foot = foot.union(LineString([sp["anchor"],sp["screw"]]).buffer(8,quad_segs=24))
        assert foot.geom_type == "Polygon"
        outside = core.buffer(GAP+WALL, quad_segs=12).intersection(
            veneer.buffer(GAP+WALL, quad_segs=12)).intersection(win)
        outside=outside.difference(sp.get("exclusion",Polygon()))
        normal = outside.difference(core.buffer(GAP, quad_segs=12).union(
                                    veneer.buffer(GAP, quad_segs=12)))
        relief = outside.difference(core.buffer(.85, quad_segs=12).union(
                                    veneer.buffer(.85, quad_segs=12)))
        base = prism(foot, 0, BASE)
        body = base + prism(normal, BASE-.0001, BASE+8.0)
        body += prism(relief, BASE+8.0-.0001, BASE+9.2)
        # 45 degree return from the squeeze-out recess; no unsupported roof.
        for z, c in [(9.2, .65), (9.4, .45), (9.6, .25), (9.8, GAP)]:
            ring = outside.difference(core.buffer(c, quad_segs=12).union(
                                      veneer.buffer(c, quad_segs=12)))
            body += prism(ring, BASE+z-.0001, BASE+z+.2)
        body += prism(normal, BASE+10.0-.0001, BASE+GUIDE_TOP)
        label = lettering(sp["letter"], sp["label"])
        assert label.difference(foot).area < 1e-6
        body += prism(label, BASE-.01, BASE+.4)
        shaft=Point(sp["screw"]).buffer(BORE/2,quad_segs=32)
        recess=Point(sp["screw"]).buffer(COUNTERBORE/2,quad_segs=32)
        body -= prism(shaft,-.1,BASE+.1) + prism(recess,-.1,RECESS)
        m = d.mesh(body)
        assert m.is_volume and len(body.decompose()) == 1, sp["name"]
        result.append(dict(**sp, foot=foot, wall=normal, body=body, mesh=m,
                           shaft=shaft,recess=recess))
    return result


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    before = protected()
    f, mm, core, veneer, region, sources, error = extract()
    ss = json.loads(files(COMPANION, False)["Metadata/project_settings.config"])
    for k, v in LOCKED.items():
        assert ss[k] == v, (k, ss.get(k))
    baseline = copy.deepcopy(ss)
    ss["print_settings_id"] = f"Dara center veneer alignment jig {REV} - 8% gyroid"
    # Use the saved A1 machine/material configuration intact. The project
    # writer's original package metadata is explicitly redirected to production.
    d.source = lambda: f
    d.source_path = lambda: SOURCE
    pieces = shoes(core, veneer)
    entries, checks = [], []
    core_solid = None
    for i in range(1, 6):
        b = d.solid(mm[f"C{i}"])
        core_solid = b if core_solid is None else core_solid+b
    visible_veneer = d.solid(mm["V3"]) ^ prism(region, 8.6, 13)
    for sp in pieces:
        m, b = sp["mesh"], sp["body"]
        assert abs(m.bounds[0, 2]) < 1e-6
        # In-use positions: production M elevated by the shoes' common base.
        core_overlap = abs((b ^ core_solid.translate([0, 0, BASE])).volume())
        veneer_overlap = abs((b ^ visible_veneer.translate([0, 0, BASE])).volume())
        assert max(core_overlap, veneer_overlap) < 1e-4, sp["name"]
        contact = filled(mesh_slice(mm["C3"], .01)) if sp["letter"] == "B" else core
        support = sp["foot"].intersection(contact).area
        assert support > 350
        local_region = region.intersection(sp["window"])
        # Guide tops must remain below even the lowest edge of the front.
        v = mm["V3"].vertices
        sel = shapely.contains_xy(sp["window"], v[:, 0], v[:, 1]) & (
            v[:, 2] > 10.4) & (v[:, 2] < 13)
        assert sel.any()
        minimum_front = float(v[sel, 2].min())
        assert minimum_front-GUIDE_TOP > .29
        # No guide at either veneer seam or any non-artwork edge.
        assert sp["wall"].distance(box(-125.01, 160, -124.99, 182)) > 9
        assert sp["wall"].distance(box(124.99, 160, 125.01, 182)) > 9
        T = d.centered(m, xy=sp["xy"])
        obj = dict(name=sp["name"]+f" - V3 alignment shoe {REV}",
                   parts=[dict(mesh=m, settings=dict(extruder="1"))],
                   transform=T,
                   settings=dict(extruder="1", brim_width="1", enable_support="1"))
        entries.append(obj)
        standalone = m.copy()
        standalone.apply_translation([-m.bounds[0, 0], -m.bounds[0, 1], 0])
        stl = OUT/f"V3-Jig-{REV}-{sp['letter']}.stl"
        standalone.export(stl)
        retention=check_retention(sp,mm)
        checks.append(dict(
            piece=sp["letter"], source_window_xy_mm=list(sp["window"].bounds),
            size_mm=m.extents.tolist(), stl_sha256=d.sha(stl),
            connected_solids=len(b.decompose()), watertight=m.is_watertight,
            positive_volume=m.is_volume,
            base_contact_area_mm2=sp["foot"].difference(sp["recess"]).area,
            supported_core_area_mm2=support,
            screw_retention=retention,
            assembled_core_intersection_mm3=core_overlap,
            assembled_veneer_intersection_mm3=veneer_overlap,
            minimum_front_edge_clearance_above_guide_mm=minimum_front-GUIDE_TOP,
            datum_relief=(dict(apex_xy_mm=sp["apex"],apex_radius_mm=2,
                              core_seam_end_xy_mm=sp["seam_end"],
                              core_seam_relief_radius_mm=3)
                          if sp["letter"]=="V" else None),
            geometry= dict(foot=mapping(sp["foot"]), wall=mapping(sp["wall"]))))
    records = d.write_project(EDIT, [entries], ss["print_settings_id"], ss)
    assert before == protected(), "Protected production file changed"
    diff = {k: dict(old=baseline.get(k), new=v) for k,v in ss.items()
            if baseline.get(k) != v}
    d.save_json(OUT/"geometry-validation.json", dict(
        revision=REV, purpose="V-crotch datum aligns V3 to assembled M; weights clamp",
        source_project=str(SOURCE), source_sha256=d.sha(SOURCE),
        profile_project=str(COMPANION), profile_sha256=d.sha(COMPANION),
        source_objects=sources, actual_veneer_section_vs_plan_area_error_mm2=error,
        source_section_z_mm=dict(core=4, veneer=9.5),
        base_thickness_mm=BASE, clearance_per_side_mm=GAP,
        maximum_nominal_relative_play_normal_to_each_guide_mm=2*GAP,
        coordinate_play_note="0.30 mm is normal to each flank, not a 2D position bound; V angle couples XY movement.",
        changed_variable="Add rear arms, existing-screw attachment, recessed heads and a common 10.4 mm base; retain r2 contour guides.",
        nominal_guide_top_above_core_back_mm=GUIDE_TOP,
        core_height_mm=8.4, veneer_back_mm=8.6, minimum_veneer_edge_mm=10.5,
        glue_relief=dict(assembly_z_mm=[8.0,9.2], setback_mm=.85,
                         ramp_to_normal_assembly_z_mm=[9.2,10.0]),
        pieces=checks, placements=records, editable_sha256=d.sha(EDIT),
        project_settings_differences_from_saved_A1_companion=diff,
        intentional_object_settings=dict(extruder="1", brim_width="1",
                                         enable_support="1"),
        support_purpose="Back underside counterbore roofs; removable before assembly.",
        locked_settings=LOCKED, protected_files_before=before,
        protected_files_after=protected(), physical_fit_pending=True,
        physical_clamping_load_not_qualified=True))
    draw(pieces, core, veneer)
    print("Built two shoes on one A1 plate:", EDIT, flush=True)


def check_retention(sp,mm):
    """Check actual saved pilot, jig clearance and the specified hardware stack."""
    p=Point(sp["screw"])
    core=mm[sp["core_name"]]
    underhead=RECESS-WASHER_THICKNESS
    tip=underhead+SCREW_LENGTH
    engagement=tip-BASE
    assert 5<engagement<6 and underhead-HEAD_HEIGHT>=.49
    hole_checks=[]
    for z in [.15,1.,4.,engagement-.1,8.3]:
        section=mesh_slice(core,z)
        assert not section.covers(p)
        radius=p.distance(section)
        assert 1.57<radius<1.60,(sp["letter"],z,radius)
        # Require a full collar around the pilot, not just a nearby empty area.
        collar=p.buffer(4.9,quad_segs=32).difference(p.buffer(1.6,quad_segs=32))
        assert collar.difference(section).area<.001
        hole_checks.append(dict(core_z_mm=z,minimum_pilot_radius_mm=radius))
    shank=prism(p.buffer(1.75,quad_segs=32),underhead,tip)
    washer=prism(p.buffer(5,quad_segs=32).difference(p.buffer(2.2,quad_segs=32)),
                 underhead,RECESS)
    head=prism(p.buffer(3.5,quad_segs=32),underhead-HEAD_HEIGHT,underhead)
    collision=abs((sp["body"]^(shank+washer+head)).volume())
    assert collision<1e-5
    seat=mesh_slice(sp["mesh"],RECESS+.05)
    bearing=p.buffer(5,quad_segs=32).difference(p.buffer(2.25,quad_segs=32))
    assert bearing.difference(seat).area<1e-4
    return dict(existing_core=sp["core_name"],existing_pilot_xy_mm=list(sp["screw"]),
                actual_source_pilot_sections=hole_checks,
                hardware="#6-19 x 1/2 inch plastic thread-forming pan-head screw; 10 mm OD x 1 mm washer",
                screw_under_head_length_mm=SCREW_LENGTH,
                nominal_head_diameter_mm=7,nominal_head_height_mm=HEAD_HEIGHT,
                shaft_clearance_diameter_mm=BORE,counterbore_diameter_mm=COUNTERBORE,
                counterbore_depth_mm=RECESS,seat_thickness_mm=BASE-RECESS,
                thread_engagement_mm=engagement,
                tip_clearance_to_core_front_mm=BASE+8.4-tip,
                tip_clearance_to_veneer_back_mm=BASE+8.6-tip,
                head_clearance_above_table_mm=underhead-HEAD_HEIGHT,
                hardware_to_jig_intersection_mm3=collision,
                bearing_annulus_supported=True)


def draw(pieces, core, veneer):
    fig = plt.figure(figsize=(13, 8), facecolor="#f5f3ef")
    ax = fig.add_axes([.04, .12, .54, .79])
    def poly(ax, g, **kw):
        for p in ([g] if g.geom_type=="Polygon" else g.geoms):
            x,y=p.exterior.xy;ax.fill(x,y,**kw)
    poly(ax, core, color="#d6d7d5", zorder=1)
    poly(ax, veneer, color="#bb7d4e", zorder=2)
    for sp in pieces:
        poly(ax, sp["foot"], color="#268f9e", alpha=.65,zorder=3)
        poly(ax, sp["wall"], color="#15545f",zorder=4)
        ax.plot(*sp["screw"],"o",color="#172b35",markersize=5,zorder=5)
        tx,ty=sp["label"]
        ax.annotate(sp["letter"], (tx,ty), xytext=(tx+(-60 if tx<0 else 60),ty+26),
                    fontsize=15,weight="bold",color="#15545f",
                    arrowprops=dict(arrowstyle="-",color="#15545f"),ha="center")
    ax.set_aspect("equal");ax.set_xlim(-325,325);ax.set_ylim(-210,222)
    ax.axis("off")
    fig.text(.04,.955,f"Screw-retained veneer guides · A1 · {REV}",fontsize=22,weight="bold",color="#243b41")
    fig.text(.04,.91,"Copper: V3 veneer     Gray: assembled cores     Teal: two removable shoes",fontsize=11)
    for n,sp in enumerate(pieces):
        a=fig.add_axes([.64,.56-n*.34,.30,.30])
        poly(a,sp["foot"],color="#76b5bc")
        # Exact outlines at the assembly; the open ends are not locating faces.
        v=veneer.intersection(sp["window"])
        poly(a,v,color="#bb7d4e",alpha=.65)
        poly(a,sp["wall"],color="#15545f")
        poly(a,sp["recess"],color="#eeeeea")
        poly(a,sp["shaft"],color="#172b35")
        a.text(*sp["label"],sp["letter"],ha="center",va="center",weight="bold",color="white")
        a.set_aspect("equal");a.axis("off")
        a.set_title(sp["name"],fontsize=12,loc="left")
    fig.text(.04,.065,"Fasten each guide from underneath using one existing mounting screw and washer; lower V3 between the guides.",fontsize=11)
    fig.text(.04,.035,"Black dots: existing screw holes · 0.15 mm clearance per side · heads recessed · top face clear for weights",fontsize=11)
    fig.savefig(OUT/f"V3-Jig-{REV}-layout.png",dpi=160)
    plt.close(fig)
    draw_solids(pieces)
    draw_hardware()


def draw_hardware():
    from matplotlib.patches import Rectangle
    fig,ax=plt.subplots(figsize=(10,6),facecolor="#f5f3ef")
    ax.set_facecolor("#f5f3ef")
    def rect(x,z,w,h,c):
        ax.add_patch(Rectangle((x,z),w,h,facecolor=c,edgecolor="none"))
    for side in [-1,1]:
        rect(-9 if side<0 else 6,0,3,RECESS,"#76b5bc")
        rect(-9 if side<0 else BORE/2,RECESS,9-BORE/2,BASE-RECESS,"#76b5bc")
        rect(-12 if side<0 else 1.5875,BASE,12-1.5875,8.4,"#c5c7c8")
    rect(-12,BASE+8.6,24,1.9,"#bb7d4e")
    underhead=RECESS-WASHER_THICKNESS
    rect(-5,underhead,10,WASHER_THICKNESS,"#d3ad54")
    rect(-3.5,underhead-HEAD_HEIGHT,7,HEAD_HEIGHT,"#5f6870")
    rect(-1.75,underhead,3.5,SCREW_LENGTH,"#5f6870")
    ax.axhline(0,color="#263c44",lw=1)
    ax.annotate("Existing 1/2-inch mounting screw\nand 1 mm washer",(0,3),(-25,4),
                arrowprops=dict(arrowstyle="->"),fontsize=11,ha="right")
    ax.annotate("5.3 mm into existing core pilot",(0,13.5),(18,13.5),
                arrowprops=dict(arrowstyle="->"),fontsize=11)
    ax.annotate("Head recessed 0.5 mm\nabove the table",(0,.5),(18,2),
                arrowprops=dict(arrowstyle="->"),fontsize=11)
    ax.text(-20,BASE+4,"Core",ha="center",fontsize=12)
    ax.text(-20,BASE+9.1,"Veneer",ha="center",fontsize=12)
    ax.text(-20,7,"Jig",ha="center",fontsize=12)
    ax.text(18,BASE+9.2,"Screw tip stays 3.3 mm\nbelow veneer back.",fontsize=11)
    ax.set_xlim(-48,48);ax.set_ylim(-2,25);ax.set_aspect("equal");ax.axis("off")
    ax.set_title("Section through either mounting screw",fontsize=19,weight="bold",pad=18)
    fig.text(.5,.08,"Nominal hardware envelope; actual screw head dimensions and physical fit still need checking.",
             ha="center",fontsize=10)
    fig.savefig(OUT/f"V3-Jig-{REV}-screw-section.png",dpi=160,bbox_inches="tight")
    plt.close(fig)


def draw_solids(pieces):
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from matplotlib.colors import to_rgb
    fig=plt.figure(figsize=(14,5),facecolor="#f5f3ef")
    light=np.array([-.35,-.45,.82]);light/=np.linalg.norm(light)
    for i,sp in enumerate(pieces):
        ax=fig.add_subplot(1,len(pieces),i+1,projection="3d",facecolor="#f5f3ef")
        m=sp["mesh"].copy()
        m.apply_translation([-m.bounds[:,0].mean(),-m.bounds[:,1].mean(),0])
        shade=.55+.45*np.maximum(0,m.face_normals@light)
        colors=np.array(to_rgb("#4b9eab"))[None,:]*shade[:,None]
        coll=Poly3DCollection(m.triangles,facecolors=colors,edgecolors="none",
                              linewidths=0,rasterized=True)
        ax.add_collection3d(coll)
        lo,hi=m.bounds
        ax.set_xlim(lo[0]-2,hi[0]+2);ax.set_ylim(lo[1]-2,hi[1]+2)
        ax.set_zlim(0,BASE+GUIDE_TOP);ax.set_box_aspect([m.extents[0],m.extents[1],BASE+GUIDE_TOP])
        ax.view_init(elev=28,azim=-65 if i!=2 else -70)
        ax.axis("off");ax.set_title(sp["name"],fontsize=14)
    fig.suptitle("Printable guides with rear mounting arms and recessed screw heads",
                 fontsize=19,weight="bold",color="#243b41")
    fig.text(.5,.045,"Both print together in white PLA. Teal is used here to show the geometry.",
             fontsize=11,ha="center")
    fig.subplots_adjust(left=.02,right=.98,top=.88,bottom=.12,wspace=.03)
    fig.savefig(OUT/f"V3-Jig-{REV}-shoes.png",dpi=160)
    plt.close(fig)


def native():
    folder=WORK/"native";folder.mkdir(exist_ok=True)
    with (folder/"slice.log").open("w") as log:
        p=subprocess.run([str(EXE),"--slice","1","--export-3mf","sliced.3mf",
                          "--outputdir",str(folder),str(EDIT)],
                         cwd=EXE.parent,stdout=log,stderr=subprocess.STDOUT,
                         creationflags=subprocess.CREATE_NO_WINDOW)
    print("Native slicer exit:",p.returncode,flush=True)
    assert p.returncode==0
    validate(folder)


def project_entries(f):
    cfg=ET.fromstring(f["Metadata/model_settings.config"])
    root=ET.fromstring(f["3D/3dmodel.model"])
    result={}
    for co in cfg.findall("object"):
        parts,st=d.read_object(f,co.get("id"))
        T=d.transform(next(i for i in root.find(d.tag("build"))
                           if i.get("objectid")==co.get("id")).get("transform"))
        result[st["name"]]=dict(parts=parts,settings=st,T=T)
    return result


def extrusions(text):
    """Read actual linear extrusion moves, including removable supports."""
    x=y=z=e=0.
    rel_e=rel_xyz=False
    feature="Custom"
    width=.5
    for raw in text.splitlines():
        if raw.startswith("; FEATURE: "):feature=raw.split(": ",1)[1]
        if raw.startswith("; LINE_WIDTH: "):width=float(raw.split(": ",1)[1])
        code=raw.split(";",1)[0].strip()
        if not code:continue
        cmd=code.split()[0]
        v={k:float(n) for k,n in TOKEN.findall(code)}
        if cmd=="M83":rel_e=True
        elif cmd=="M82":rel_e=False
        elif cmd=="G90":rel_xyz=False
        elif cmd=="G91":rel_xyz=True
        elif cmd=="G92":
            x,y,z,e=[v.get(k,old) for k,old in zip("XYZE",(x,y,z,e))]
        elif cmd in ["G0","G1","G2","G3"]:
            nx,ny,nz=[old+v.get(k,0) if rel_xyz else v.get(k,old)
                      for k,old in zip("XYZ",(x,y,z))]
            de=v.get("E",0) if rel_e else v.get("E",e)-e
            if de>0 and feature!="Custom" and np.hypot(nx-x,ny-y)>.001:
                assert cmd in ["G0","G1"],"Unexpected model arc"
                yield round(nz,2),LineString([(x,y),(nx,ny)]).buffer(width/2,quad_segs=4),feature
            x,y,z=nx,ny,nz
            e=e+v.get("E",0) if rel_e else v.get("E",e)


def support_paths(text,entries,proof):
    """Verify local native backing, roof continuity, and access for cleanup."""
    rows=list(extrusions(text))
    result=[]
    fig,axs=plt.subplots(1,2,figsize=(10,5),facecolor="#f5f3ef")
    for ax,(name,row) in zip(axs,entries.items()):
        sp=next(p for p in proof["pieces"] if p["piece"]==name[0])
        p=Point(np.array(sp["screw_retention"]["existing_pilot_xy_mm"])+row["T"][:2,3])
        pocket=p.buffer(COUNTERBORE/2,quad_segs=32)
        supports=[(z,g,f) for z,g,f in rows if f.startswith("Support") and g.intersects(pocket)]
        assert supports,(name,"No actual support in counterbore")
        zs=sorted(set(z for z,g,f in supports))
        top=max(zs)
        assert abs(RECESS-top-.2)<.02,(name,top)
        interface=union_all([g for z,g,f in supports if z==top])
        roof=union_all([g for z,g,f in rows if abs(z-(RECESS+.2))<.01
                        and not f.startswith("Support") and g.intersects(pocket)])
        bearing=p.buffer(5,quad_segs=32).difference(p.buffer(BORE/2+.1,quad_segs=32))
        roof_coverage=roof.intersection(bearing).area/bearing.area
        assert roof_coverage>.95,(name,"Incomplete washer seat",roof_coverage)
        # Dense interface need not cover every point; short gaps are bridged.
        samples=shapely.points(shapely.get_coordinates(bearing))
        max_gap=float(shapely.distance(samples,interface).max())
        assert max_gap<1.0,(name,"Counterbore backing too sparse",max_gap)
        for geom,color,alpha in [(pocket,"#eeeeea",1),(roof.intersection(pocket),"#76b5bc",.6),
                                 (interface,"#cf9149",.9)]:
            for g in ([geom] if geom.geom_type=="Polygon" else geom.geoms):
                if g.geom_type!="Polygon":continue
                ax.fill(*g.exterior.xy,color=color,alpha=alpha)
                for ring in g.interiors:ax.fill(*ring.xy,color="#f5f3ef")
        ax.set_aspect("equal")
        ax.set_xlim(p.x-7,p.x+7);ax.set_ylim(p.y-7,p.y+7);ax.axis("off")
        ax.set_title(name[0]+" · screw recess",fontsize=14)
        result.append(dict(piece=name[0],support_layer_top_z_mm=zs,
                           roof_underside_z_mm=RECESS,
                           support_top_gap_mm=RECESS-top,
                           washer_seat_first_layer_coverage_fraction=roof_coverage,
                           bearing_boundary_max_distance_to_interface_mm=max_gap,
                           actual_support_extrusions=len(supports)))
    fig.suptitle("Native screw-seat toolpaths: roof in teal, support interface in gold",fontsize=14)
    fig.text(.5,.05,"Underside recesses open to the bed for support removal before fitting screws.",
             ha="center",fontsize=11)
    fig.savefig(OUT/f"V3-Jig-{REV}-support-check.png",dpi=160)
    plt.close(fig)
    return result


def guide_paths(text, entries):
    """Inspect native beads at the side guides and every relief transition."""
    x=y=z=e=0.
    rel_e=rel_xyz=False
    feature="Custom"
    width=.5
    rows=collections.defaultdict(list)
    special=collections.defaultdict(collections.Counter)
    for raw in text.splitlines():
        if raw.startswith("; FEATURE: "):feature=raw.split(": ",1)[1]
        if raw.startswith("; LINE_WIDTH: "):width=float(raw.split(": ",1)[1])
        code=raw.split(";",1)[0].strip()
        if not code:continue
        cmd=code.split()[0]
        v={k:float(n) for k,n in TOKEN.findall(code)}
        if cmd=="M83":rel_e=True
        elif cmd=="M82":rel_e=False
        elif cmd=="G90":rel_xyz=False
        elif cmd=="G91":rel_xyz=True
        elif cmd=="G92":
            x,y,z,e=[v.get(k,old) for k,old in zip("XYZE",(x,y,z,e))]
        elif cmd in ["G0","G1","G2","G3"]:
            nx,ny,nz=[old+v.get(k,0) if rel_xyz else v.get(k,old)
                      for k,old in zip("XYZ",(x,y,z))]
            de=v.get("E",0) if rel_e else v.get("E",e)-e
            if de>0 and feature not in ["Custom","Brim","Support","Support interface"] and np.hypot(nx-x,ny-y)>.001:
                assert cmd in ["G0","G1"],"Unexpected model arc"
                zz=round(nz,2)
                if zz>=BASE+.2-.001:
                    rows[zz].append(([(x,y),(nx,ny)],width,feature))
                if feature in ["Floating vertical shell","Bridge"]:
                    special[feature][zz]+=1
            x,y,z=nx,ny,nz
            e=e+v.get("E",0) if rel_e else v.get("E",e)
    _,_,core,veneer,_,_,_=extract()
    checked=[]
    for name,row in entries.items():
        T=row["T"]
        m=row["parts"][0]["mesh"].copy();m.apply_transform(T)
        lo,hi=m.bounds
        label=name[0]
        # The editable meshes retain assembly coordinates; T is only a
        # translation for these upright shoes.
        assert np.allclose(T[:3,:3],np.eye(3))
        from shapely import affinity
        fit=affinity.translate(core.union(veneer),*T[:2,3])
        beadrows={}
        for zz,segments in rows.items():
            lines=[LineString(xy).buffer(w/2,quad_segs=4)
                   for xy,w,feature in segments
                   if lo[0]-.5<=xy[0][0]<=hi[0]+.5 and lo[1]-.5<=xy[0][1]<=hi[1]+.5]
            if lines:beadrows[zz]=union_all(lines)
        assert round(BASE+GUIDE_TOP,2) in beadrows
        # Skip the embossed letters just above the base.
        critical=[round(BASE+h,2) for h in [1.8,7.8,8.4,9.2,9.4,9.6,9.8,10,10.2]]
        clearances=[]
        for zz in critical:
            beads=beadrows[zz]
            overlap=beads.intersection(fit).area
            assert overlap<.0001,(label,zz,overlap)
            clearance=beads.distance(fit)
            assert clearance>.08,(label,zz,clearance)
            clearances.append(dict(z_mm=zz,bead_clearance_mm=clearance))
        # At each returning ledge layer, inspect native bead areas against the
        # complete preceding mesh section, rather than interpreting a feature
        # label as a floating-region warning.
        overhang=[]
        for zz in [round(BASE+h,2) for h in [9.4,9.6,9.8,10,10.2]]:
            below=mesh_slice(m,zz-.3)
            beads=beadrows[zz]
            distance=0.
            for g in ([beads] if beads.geom_type=="Polygon" else beads.geoms):
                coords=np.array(g.exterior.coords)
                distance=max(distance,float(shapely.distance(shapely.points(coords),below).max()))
            assert distance<.29,(label,zz,distance)
            overhang.append(dict(z_mm=zz,max_bead_edge_beyond_previous_layer_mm=distance))
        checked.append(dict(piece=label,guide_bead_clearances=clearances,
                            relief_ramp_overhangs=overhang))
    return dict(shoes=checked,special_feature_layers={
        k:{str(z):n for z,n in sorted(v.items())} for k,v in special.items()},
        note="Bridge and Floating vertical shell are infill feature names. "
             "The slicer warning field is empty; guide ledges have <=0.29 mm "
             "horizontal advance per 0.20 mm layer.")


def validate(folder,publish=True):
    proof=json.loads((OUT/"geometry-validation.json").read_text())
    assert proof["editable_sha256"]==d.sha(EDIT)
    assert proof["protected_files_before"]==protected()
    result=json.loads((folder/"result.json").read_text())
    assert result["return_code"]==0,result
    f=files(folder/"sliced.3mf");s=json.loads(f["Metadata/project_settings.config"])
    for k,v in LOCKED.items():assert s[k]==v,(k,s.get(k))
    ef=files(EDIT);es=json.loads(ef["Metadata/project_settings.config"])
    baseline=json.loads(files(COMPANION,False)["Metadata/project_settings.config"])
    machine_keys=["machine_start_gcode","machine_end_gcode","change_filament_gcode",
                  "layer_change_gcode","time_lapse_gcode"]
    for k in machine_keys:assert s[k]==es[k]==baseline[k],k
    assert s["filament_settings_id"]==baseline["filament_settings_id"]
    assert s["filament_colour"]==baseline["filament_colour"]
    a,b=project_entries(ef),project_entries(f)
    assert a.keys()==b.keys() and len(a)==2
    roundtrip=[]
    for name, row in a.items():
        for r in [row,b[name]]:
            for k,v in LOCKED.items():assert r["settings"].get(k,s[k])==v,(name,k)
            assert r["settings"]["extruder"]=="1"
            assert r["settings"]["enable_support"]=="1"
            for part in r["parts"]:
                for k,v in LOCKED.items():assert part["settings"].get(k,r["settings"].get(k,s[k]))==v
        def vertices(r):
            vv=np.concatenate([x["mesh"].vertices for x in r["parts"]])
            return vv@r["T"][:3,:3].T+r["T"][:3,3]
        av,bv=vertices(row),vertices(b[name])
        e=max(cKDTree(av).query(bv)[0].max(),cKDTree(bv).query(av)[0].max())
        assert e<.001,(name,e)
        roundtrip.append(dict(name=name,maximum_mesh_pose_error_mm=float(e)))
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
    for k,v in LOCKED.items():
        assert config.get(k)==(";".join(v) if isinstance(v,list) else v),(k,config.get(k))
    scan=scan_gcode(text)
    assert scan["conservative_bed_edge_clearance_mm"]>2
    assert not scan["features"].get("Prime tower",0)
    assert scan["features"].get("Support",0)>0
    assert set(scan["model_extrusion_z_by_filament_mm"])=={"1"}
    assert "; EXECUTABLE_BLOCK_END" in text
    # Check native extrusion through each glue-relief transition and guide band.
    layers=scan["model_extrusion_z_by_filament_mm"]["1"]
    for h in [BASE,BASE+8,BASE+9.2,BASE+GUIDE_TOP]:
        assert any(abs(z-h)<.001 for z in layers),h
    log=(folder/"slice.log").read_text(errors="replace")
    suspicious=[ln for ln in log.splitlines()
                if any(w in ln.lower() for w in ["floating","collision","non-manifold","empty layer"])]
    assert not suspicious,suspicious
    est=result["sliced_plates"][0]
    assert not est.get("warning_message"),est.get("warning_message")
    guide_checks=guide_paths(text,a)
    support_checks=support_paths(text,a,proof)
    report=dict(
        revision=REV,editable_sha256=d.sha(EDIT),
        native_sha256=d.sha(folder/"sliced.3mf"),
        native_return_code=0,slicer_result=result,
        machine_gcode_keys_verified=machine_keys,locked_settings=s and LOCKED,
        all_object_and_volume_overrides_checked=True,mesh_roundtrip=roundtrip,
        gcode_sha256=hashlib.sha256(gb).hexdigest(),gcode_md5=checksum,
        gcode_configuration_checked=True,toolpaths=scan,
        suspicious_native_log_lines=suspicious,
        native_warning_message=est.get("warning_message",""),
        actual_guide_toolpath_checks=guide_checks,
        actual_counterbore_support_checks=support_checks,
        estimate_seconds=est["total_predication"],
        estimate_grams=sum(v["total_used_g"] for v in est["filaments"]),
        protected_files_after=protected(),physical_fit_pending=True,
        generator_sha256=d.sha(Path(__file__)))
    if publish:
        d.save_json(OUT/"native-validation.json",report)
        shutil.copyfile(folder/"sliced.3mf",FINAL)
        print("Validated and saved:",FINAL,flush=True)
    print("Estimate:",report["estimate_seconds"],"s",report["estimate_grams"],"g",flush=True)
    return report


def reopen():
    """Reopen and reslice the delivered project without replacing it."""
    folder=WORK/"reopen";folder.mkdir(exist_ok=True)
    original=d.sha(FINAL)
    with (folder/"slice.log").open("w") as log:
        p=subprocess.run([str(EXE),"--slice","1","--export-3mf","sliced.3mf",
                          "--outputdir",str(folder),str(FINAL)],
                         cwd=EXE.parent,stdout=log,stderr=subprocess.STDOUT,
                         creationflags=subprocess.CREATE_NO_WINDOW)
    print("Reopen/reslice exit:",p.returncode,flush=True)
    assert p.returncode==0
    checked=validate(folder,publish=False)
    assert d.sha(FINAL)==original
    report=json.loads((OUT/"native-validation.json").read_text())
    report["native_reopen_validation"]=dict(
        method="Reopen final project and natively reslice plate 1",
        input_sha256=original,return_code=0,
        warning_message=checked["native_warning_message"],
        mesh_roundtrip=checked["mesh_roundtrip"],
        locked_settings=checked["locked_settings"],
        actual_counterbore_support_checks=checked["actual_counterbore_support_checks"])
    report["generator_sha256"]=d.sha(Path(__file__))
    d.save_json(OUT/"native-validation.json",report)
    shutil.copyfile(Path(__file__),OUT/f"build_center_veneer_alignment_jig_{REV}.py")
    print("Saved final-project reopen verification.",flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=["build","slice","validate","reopen"])
    args=p.parse_args()
    if args.action=="build":build()
    elif args.action=="slice":native()
    elif args.action=="reopen":reopen()
    else:validate(WORK/"native")
