"""Read current embedded joint triangles and commanded key/pocket toolpaths.

The toolpath envelopes are idealized commanded widths, not measurements of
deposited PLA, shrinkage, support removal or physical fit.
"""
import collections
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / '.work/python-libs'), str(ROOT / 'scripts')]
import numpy as np
import trimesh
import manifold3d as mf
import shapely
from shapely import affinity
from shapely.geometry import box, LineString, Point
from organize_root_projects import rows
from development_3mf import solid
from mesh_sections import mesh_slice
from validate_print_project import TOKEN
from remove_unused_project_filaments import dump, digest

WORK = ROOT / '.work/knot-infill-first-revert-r1'
REPORT = ROOT / 'release/knot-infill-first-revert-r1'
PLAN = ROOT / 'working/bambu/Dara-Photo-Frame-A2L/production-plan.json'


def local(g, joint):
    return affinity.rotate(affinity.translate(g, -joint[2][0], -joint[2][1]), -joint[3], origin=(0, 0))


def vertical_hits(mesh, xy):
    t = mesh.triangles
    a, b, c = t[:, 0], t[:, 1], t[:, 2]
    u, v, q = b-a, c-a, np.array(xy)-a[:, :2]
    det = u[:, 0]*v[:, 1]-u[:, 1]*v[:, 0]
    good = abs(det) > 1e-10
    aa = np.zeros(len(t)); bb = np.zeros(len(t))
    aa[good] = (q[good, 0]*v[good, 1]-q[good, 1]*v[good, 0])/det[good]
    bb[good] = (u[good, 0]*q[good, 1]-u[good, 1]*q[good, 0])/det[good]
    hit = good & (aa >= -1e-8) & (bb >= -1e-8) & (aa+bb <= 1+1e-8)
    return sorted(set(np.round((a[:, 2]+aa*u[:, 2]+bb*v[:, 2])[hit], 7)))


def geometry(project):
    _, objects = rows(project)
    parts = [[p['mesh'] for p in o['parts'] if p['subtype'] == 'normal_part'] for o in objects]
    meshes = [trimesh.util.concatenate(ps) for ps in parts]
    bodies = [mf.Manifold.batch_boolean([solid(m) for m in ps], mf.OpType.Add) for ps in parts]
    plan = json.loads(PLAN.read_text())
    heights = [5.1, 5.3, 5.5, 5.7, 5.9]
    sections = {(i, z): shapely.union_all([mesh_slice(m, z) for m in ps]) for i, ps in enumerate(parts) for z in heights}
    records = []
    for ji, j in enumerate(plan['frame_joints'], 1):
        intersection = bodies[j[0]] ^ bodies[j[1]]
        collision = abs(intersection.volume())
        # Native saves round individual volume coordinates. Report these
        # slivers explicitly and require every connected overlap to be thinner
        # than the mesh-roundtrip tolerance, rather than claiming exact zero.
        aa = math.radians(j[3]); nn = np.array([math.cos(aa), math.sin(aa)]); tt = np.array([-nn[1], nn[0]])
        slivers = []
        for component in intersection.decompose():
            vertices = component.to_mesh64().vert_properties[:, :3]
            if not len(vertices): continue
            v = np.column_stack([(vertices[:, :2]-j[2])@np.column_stack([nn, tt]), vertices[:, 2]])
            thickness = float(np.ptp(v, axis=0).min())
            assert thickness < .0001, (ji, collision, thickness)
            slivers.append(thickness)
        keys = []
        angle = math.radians(j[3]); n = np.array([math.cos(angle), math.sin(angle)]); tangent = np.array([-n[1], n[0]])
        for ki, y in enumerate(j[5], 1):
            probes = []
            for z in heights:
                male, female = [local(sections[(i, z)], j) for i in j[:2]]
                window = box(1, y-3.5, 17, y+3.5)
                key = male.intersection(window)
                assert key.area > 30
                sidegap = key.distance(female)
                assert sidegap > .14, (ji, ki, z, sidegap)
                for x in [3.5, 9, 14.5]:
                    line = LineString([(x, y-3.5), (x, y+3.5)])
                    a = male.intersection(line); b = line.difference(female)
                    assert a.geom_type in ('LineString','MultiLineString') and b.geom_type in ('LineString','MultiLineString'), (ji, ki, z, x)
                    if b.geom_type=='MultiLineString':
                        containing=[g for g in b.geoms if g.distance(Point(x,y))<.0001]
                        assert len(containing)==1,(ji,ki,z,x,b.wkt)
                        b=containing[0]
                    # Separate normal volumes can leave micron-scale gaps
                    # after serialization; measure the exterior span and log
                    # the gap instead of changing or welding release meshes.
                    key_width = a.bounds[3]-a.bounds[1]; groove_width = b.bounds[3]-b.bounds[1]
                    assert key_width-a.length < .0001 and groove_width-b.length < .0001, (ji,ki,z,x,a.wkt,b.wkt)
                    assert abs(key_width-3) < .001
                    assert groove_width-key_width > .29
                    probes.append(dict(z_mm=z, x_mm=x, key_width_mm=key_width,
                        groove_width_mm=groove_width, minimum_section_clearance_mm=sidegap))
            xy = np.array(j[2])+n*9+tangent*y
            male_z, female_z = [vertical_hits(meshes[i], xy) for i in j[:2]]
            top = max(male_z); roof = min(h for h in female_z if h > 4.8)
            assert abs(top-6.0) < .001 and abs(roof-6.3) < .001, (ji, ki, male_z, female_z)
            keys.append(dict(key=ki, center_local_y_mm=y, transverse_probes=probes,
                key_top_mm=top, groove_roof_mm=roof, nominal_vertical_clearance_mm=roof-top))
        records.append(dict(joint=ji, male_plate=j[0]+1, female_plate=j[1]+1,
            assembled_interference_mm3=collision, overlap_component_minimum_thickness_mm=slivers,
            serialized_mesh_overlap_tolerance_mm=.0001, keys=keys))
        print(f'J{ji}: actual mesh clearance and both keys checked.', flush=True)
    out = dict(project_sha256=digest(project), plan_sha256=digest(PLAN),
        section_method='Original triangle/plane intersections; no regenerated key geometry',
        joints=records, joint_count=len(records), key_count=sum(len(r['keys']) for r in records),
        physical_fit_established=False)
    dump(REPORT / 'joint-geometry.json', out)
    return out


def paths_with_width(text, transform, object_id=None):
    """Positive G1 extrusion only; exclude machine routines and support/tower.

    Preserve order, tool, feature and line-width comments; map into assembly.
    """
    x=y=z=e=0.; relative=False; xyz=False; tool=None; feature='Custom'; width=None
    selected=[]; inverse=np.linalg.inv(transform); current_object=None
    excluded={'Custom', 'Support', 'Support interface', 'Support transition', 'Brim', 'Skirt', 'Prime tower'}
    for raw in text.splitlines():
        if raw.startswith('; start printing object, unique label id: '):current_object=int(raw.rsplit(': ',1)[1])
        elif raw.startswith('; stop printing object, unique label id: '):current_object=None
        if raw.startswith('; FEATURE: '): feature=raw.split(': ',1)[1]
        elif raw.startswith(('; LINE_WIDTH: ', '; WIDTH: ')): width=float(raw.split(': ',1)[1])
        code=raw.split(';',1)[0].strip()
        if not code: continue
        cmd=code.split()[0]; v={k:float(n) for k,n in TOKEN.findall(code)}
        if cmd in ['T0','T1','T2','T3']: tool=int(cmd[1:])+1
        elif cmd=='M83': relative=True
        elif cmd=='M82': relative=False
        elif cmd in ['G90','G91']: xyz=cmd=='G91'
        elif cmd=='G92': x,y,z,e=[v.get(k,o) for k,o in zip('XYZE',(x,y,z,e))]
        elif cmd in ['G0','G1','G2','G3']:
            nx,ny,nz=[o+v.get(k,0) if xyz else v.get(k,o) for k,o in zip('XYZ',(x,y,z))]
            de=v.get('E',0) if relative else v.get('E',e)-e
            if de>0 and feature not in excluded and math.hypot(nx-x,ny-y)>1e-7 and (object_id is None or current_object==object_id):
                assert cmd=='G1', 'Arc extrusion requires swept-arc handling'
                assert width is not None
                ends=np.array([[x,y,z],[nx,ny,nz]])@inverse[:3,:3].T+inverse[:3,3]
                selected.append((tool,feature,ends,width))
            x,y,z=nx,ny,nz; e=e+v.get('E',0) if relative else v.get('E',e)
    return selected


def key_paths(paths, joint, y, z):
    pool=[p for p in paths if abs(p[2][1,2]-z)<.001]
    a=np.array([p[2][:,:2] for p in pool]); assert len(a)
    angle=math.radians(joint[3]); n=np.array([math.cos(angle),math.sin(angle)]); t=np.array([-n[1],n[0]])
    a=(a-np.array(joint[2]))@np.column_stack([n,t])
    lines=shapely.linestrings(a)
    region=box(1,y-3,17,y+3)
    near=shapely.intersects(lines,region)
    selected=[(p,ln) for p,ln,yes in zip(pool,lines,near) if yes]
    assert selected
    bands=shapely.union_all([ln.buffer(p[3]/2,quad_segs=6) for p,ln in selected]).intersection(region)
    first_wall=next((i for i,(p,ln) in enumerate(selected) if p[1] in ('Outer wall','Inner wall','Overhang wall')),None)
    first_fill=next((i for i,(p,ln) in enumerate(selected) if p[1] in ('Internal solid infill','Sparse infill','Top surface','Bottom surface','Bridge','Gap infill','Floating vertical shell')),None)
    return bands,dict(first_wall=first_wall,first_fill=first_fill,
        wall_before_fill=first_wall<first_fill if first_wall is not None and first_fill is not None else None,
        features=list(dict.fromkeys(p[1] for p,ln in selected)),segments=len(selected))


def toolpaths(all_paths):
    plan=json.loads(PLAN.read_text()); records=[]
    for ji,j in enumerate(plan['frame_joints'],1):
        for ki,y in enumerate(j[5],1):
            for z in [5.2,5.4,5.6,5.8,6.0]:
                male,order=key_paths(all_paths[j[0]+1],j,y,z)
                female,_=key_paths(all_paths[j[1]+1],j,y,z)
                gap=male.distance(female); overlap=male.intersection(female).area
                assert overlap<1e-6 and gap>.05,(ji,ki,z,gap,overlap)
                if order['wall_before_fill'] is not None: assert order['wall_before_fill'],(ji,ki,z,order)
                records.append(dict(joint=ji,key=ki,z_mm=z,commanded_bead_clearance_mm=gap,
                    commanded_bead_overlap_mm2=overlap,key_path_order=order))
    result=dict(method='Idealized model extrusion bands from emitted G1 centerlines and LINE_WIDTH comments, transformed into common assembly coordinates',
        limitation='Commanded widths do not measure deposited PLA, support residue, sag, swelling or physical fit.',
        probes=records,minimum_commanded_clearance_mm=min(r['commanded_bead_clearance_mm'] for r in records),
        all_keys_wall_before_fill=True,physical_fit_established=False)
    dump(REPORT/'joint-toolpaths.json',result)
    return result


if __name__=='__main__':
    geometry(WORK/'editable.3mf')
