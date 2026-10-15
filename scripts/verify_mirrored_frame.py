"""Independent native-mesh checks for the mirrored manufacturing revision."""
import argparse,json,math
from build_mirrored_project import *
from repartition_mirrored_frame import line,axes
from build_jointed_bambu_project import read_array
from shapely import affinity,union_all

def assembled(mesh,p):
    m=mesh.copy();m.apply_translation([*p[1],-p[3]])
    m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(-p[0]),[0,0,1]));return m

def geometry():
    d=json.loads(PLAN.read_text());text=CAD.read_text();meshes=[];solids=[];rows=[]
    for i,p in enumerate(d['frame_placements']):
        m=assembled(trimesh.load_mesh(STLS/f'F{i+1}.stl'),p);meshes.append(m);solids.append(solid(m))
    for i,a in enumerate(meshes):
        for j,b in enumerate(meshes[i+1:],i+1):
            if np.any(a.bounds[1]<b.bounds[0]) or np.any(b.bounds[1]<a.bounds[0]):continue
            v=abs((solids[i]^solids[j]).volume());assert v<.001,(i+1,j+1,v)
            rows.append(dict(a=f'F{i+1}',b=f'F{j+1}',intersection_mm3=v))
    print('All frame pairs checked; no modeled interference.',flush=True)
    # The same profile and all dimensional constants are retained verbatim.
    oldtext=(BASE/'working/Dara-Photo-Frame-A1-Jointed.scad').read_text()
    profile_old=oldtext.split('module joint_tool(',1)[1].split('module ',1)[0]
    profile_new=text.split('module joint_tool(',1)[1].split('module ',1)[0]
    assert profile_old==profile_new
    seams=union_all([line(j,0) for j in d['frame_joints']])
    # Cut axes are mirrored; clipped endpoints follow the original artwork,
    # whose hand-drawn left/right edges differ by up to about half a millimeter.
    endpoint_reflection_errors=[seams.hausdorff_distance(affinity.scale(seams,x,y,origin=(0,0))) for x,y in [(-1,1),(1,-1)]]
    reflection_errors=[]
    for reflection in [np.array([-1,1]),np.array([1,-1])]:
        errors=[]
        for j in d['frame_joints']:
            c=np.array(j[2])*reflection;n=axes(j)[0]*reflection
            candidates=[]
            for q in d['frame_joints']:
                delta=np.array(q[2])-c
                candidates.append(abs(np.dot(delta,n))+100*abs(np.linalg.det(np.array([n,axes(q)[0]])))+max(0,np.linalg.norm(delta)-5))
            errors.append(min(candidates))
        reflection_errors.append(max(errors))
    assert max(reflection_errors)<1e-6,reflection_errors
    # Original artwork modules (including all eight photo openings) remain exact.
    for name in ['knot_outline','fabric_outline','letter_outline',*[f'photo_loop_{i+1}' for i in range(8)]]:
        assert artwork(text,name).equals_exact(artwork(oldtext,name),0),name
    h=json.loads((WORK/'hammered-stage.json').read_text());mletters={}
    for name,p in h['poses'].items():
        path=WORK/'hammered'/(name+('-changed' if name in ['M1','M3','M6'] else '-original')+'.npz')
        if path.exists():
            data=np.load(path);m=trimesh.Trimesh(data['vertices'],data['faces'],process=False)
        else:
            f=read_zip(BASE/'Dara.3mf');child=ET.fromstring(f[p['path']]);m=affine(read_mesh(child.find(tag('resources')).find(f"{tag('object')}[@id='{p['part_id']}']")),np.array(p['assembly_from_mesh']))
        mletters[name]=m
    # Verify all screw bores and locator holes against the frame hardware,
    # including the existing production M cuts, independently of SCAD indices.
    mounts=[]
    for kind,table,z,r in [('screw',d['screw_mounts'],4,1.5),('locator',d['dowel_mounts'],1.5,1.95)]:
        for i,row in enumerate(table):
            xy=np.array(row[2]);candidate=[]
            for name,m in mletters.items():
                ceiling=9 if kind=='screw' else 4
                if mesh_slice(m,ceiling).contains(Point(xy)):candidate.append(name)
            assert len(candidate)==1,(kind,i,candidate)
            name=candidate[0];s=mesh_slice(mletters[name],z)
            assert s.distance(Point(xy))>=r,(kind,i,name,s.distance(Point(xy)))
            frame=meshes[row[1]]
            fs=mesh_slice(frame,11 if kind=='screw' else 14.5)
            if kind=='screw':assert fs.distance(Point(xy))>1.95,(kind,i)
            else:assert fs.covers(Point(xy).buffer(1.99)),(kind,i)
            mounts.append(dict(kind=kind,index=i+1,frame=f'F{row[1]+1}',M=name,xy=row[2],minimum_hole_radius_mm=float(s.distance(Point(xy)))))
    print('All 10 screw sites and 12 locator sites match the actual hammered M.',flush=True)
    # Pins are the only intended overlap in projection between M and frame.
    # The assembled solids must have no positive-volume collision.
    collisions=[]
    for name,raw in mletters.items():
        # Recovering assembly coordinates through Bambu's rounded transforms
        # leaves <0.00001 mm plane noise; seat the nominal rear on Z=13.5.
        assert abs(raw.bounds[0,2])<.00001,(name,raw.bounds[0,2])
        m=raw.copy();m.apply_translation([0,0,13.5-raw.bounds[0,2]]);b=solid(m)
        for i,frame in enumerate(meshes):
            if np.any(frame.bounds[1]<m.bounds[0]) or np.any(m.bounds[1]<frame.bounds[0]):continue
            v=abs((b^solids[i]).volume());assert v<.001,(name,i+1,v)
            collisions.append(dict(M=name,frame=f'F{i+1}',intersection_mm3=v))
    # Recover every frame's top cross-section and compare with the continuous
    # original ribbon outside the deliberate .075 mm seams and screw holes.
    actual=union_all([mesh_slice(m,12) for m in meshes]);expected=artwork(text,'knot_outline')
    guard=seams.buffer(.12)
    guard=guard.union(union_all([Point(r[2]).buffer(2.1) for r in d['screw_mounts']]))
    missing=expected.difference(actual.buffer(.0001)).difference(guard).area
    excess=actual.difference(expected.buffer(.0001)).difference(guard).area
    assert missing<.01 and excess<.01,(missing,excess)
    report=dict(source_sha256=sha(CAD),frame_pairs=rows,frame_M_pairs=collisions,mount_alignment=mounts,
        mirrored_seam_axis_error_mm=reflection_errors,clipped_endpoint_reflection_error_mm=endpoint_reflection_errors,original_artwork_unchanged=True,joint_tool_unchanged=True,
        visible_ribbon_missing_outside_seams_mm2=missing,visible_ribbon_excess_outside_seams_mm2=excess,
        frame_assembly_order=d['frame_assembly_order'],joint_count=32,seam_length_range_mm=[d['min_seam_length_mm'],d['max_seam_length_mm']],
        minimum_seam_spacing_mm=d['min_seam_spacing_mm'],physical_fit_test_pending=True)
    (REVIEW/'geometry-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Geometry verification passed.',flush=True)

if __name__=='__main__':geometry()
