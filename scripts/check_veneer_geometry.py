"""Independent release-to-candidate checks for the development branch."""
import json
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import Point, box
from shapely import union_all

from development_3mf import *
from develop_m_veneer import texture, prism, locate, SKIN_JOINTS, CORE_BASE, SEAT_Z, POCKET_TOP, screw_clearance_tools
from add_blue_ribbon_edge import artwork
from build_jointed_bambu_project import read_array


def check():
    original=source();cad=(ROOT/'working/Dara-Photo-Frame-A1-Jointed.scad').read_text()
    outline=artwork(cad,'letter_outline');roof=texture(outline)
    poses=json.loads((ROOT/'working/geometry/hammered-M-assembly-poses.json').read_text())
    masks=union_all([locate(box(-7,-j[4]/2-5,7,j[4]/2+5),j) for j in SKIN_JOINTS])
    errors=[];count=0
    for name,p in poses.items():
        child=ET.fromstring(original[p['path']]);from colorize_print_project import read_mesh
        old=read_mesh(child.find(tag('resources')).find(f"{tag('object')}[@id='{p['part_id']}']"))
        old.apply_transform(np.array(p['assembly_from_mesh']));v=old.vertices
        # Compare native global grid vertices away from band seats and cut edges;
        # clipped triangles interpolate the height field between these vertices.
        on_grid=np.all(np.abs(v[:,:2]/.5-np.round(v[:,:2]/.5))<1e-4,axis=1)
        import shapely
        select=on_grid&(v[:,2]>10.5)&~shapely.contains(masks,shapely.points(v[:,:2]))
        q=v[select];err=np.max(np.abs(q[:,2]-roof(q[:,:2])));errors.append(float(err));count+=len(q)
    assert max(errors)<.0002,errors
    # Check the actual generated parts, including every rear recess. A planar
    # core and a planar veneer back are requirements, not merely print poses.
    flat_checks=[];clearance=screw_clearance_tools()
    for i in range(6):
        data=np.load(WORK/f'C{i+1}.npz');core=trimesh.Trimesh(data['vertices'],data['faces'],process=False)
        choose=(core.face_normals[:,2]>.99)&(core.triangles_center[:,2]<CORE_BASE+.01)&(core.triangles_center[:,2]>.1)
        faces=core.triangles[choose];assert len(faces)>0
        core_error=float(np.abs(faces[:,:,2]-CORE_BASE).max())
        assert core_error<1e-7,(i,core_error,'Core body is crowned')
        data=np.load(WORK/f'V{i+1}.npz');cap=trimesh.Trimesh(data['vertices'],data['faces'],process=False)
        rear=cap.triangles[cap.face_normals[:,2]<-.001][:,:,2]
        assert np.ptp(rear,axis=1).max()<1e-7,(i,'Sloping veneer back')
        levels=rear.mean(axis=1)
        back_error=float(np.minimum(abs(levels-SEAT_Z),abs(levels-POCKET_TOP)).max())
        assert back_error<1e-7,(i,'Nonplanar veneer back',back_error)
        v=cap.vertices;grid=np.all(abs(v[:,:2]/.5-np.round(v[:,:2]/.5))<1e-4,axis=1)
        q=v[grid&(v[:,2]>10.4)];assert len(q)>1000
        face_error=float(np.abs(q[:,2]-roof(q[:,:2])).max())
        assert face_error<.0002,(i,'Hammered front changed',face_error)
        assert (solid(cap)^clearance).volume()<1e-5,(i,'Screw-tip clearance blocked')
        flat_checks.append(dict(core=f'C{i+1}',veneer=f'V{i+1}',core_main_top_mm=CORE_BASE,
            core_body_flatness_error_mm=core_error,veneer_flat_back_mm=SEAT_Z,
            veneer_back_plane_error_mm=back_error,hammered_front_grid_error_mm=face_error,
            front_grid_vertices_checked=len(q),screw_tip_clearances_open=True))
    # The full-frame candidate's visible surface is invariant above Z8.0. All
    # modifications belong to the hidden joint volume; color modifiers are copied.
    project=OUT/'Frame-Cosmetic-Candidate-A1.3mf'
    with zipfile.ZipFile(project) as z:new={n:z.read(n) for n in z.namelist()}
    oldcfg=ET.fromstring(original['Metadata/model_settings.config']);newcfg=ET.fromstring(new['Metadata/model_settings.config'])
    source_ids={props(o).get('name','').split(' - ')[0]:o.get('id') for o in oldcfg.findall('object')}
    new_ids={props(o).get('name','').split(' cosmetic')[0]:o.get('id') for o in newcfg.findall('object')}
    placements=read_array(cad,'frame_placements');rows=[]
    upper=prism(box(-500,-500,500,500),8.0,14)
    for i,p in enumerate(placements):
        label=f'F{i+1}';a,_=read_object(original,source_ids[label]);b,_=read_object(new,new_ids[label])
        t=np.eye(4);t[:3,:3]=z_rotation(p[0]);t[:2,3]=-np.array(p[1])
        for entry in a:entry['mesh'].apply_transform(np.linalg.inv(t))
        oldbody,newbody=solid(a[0]['mesh']),solid(b[0]['mesh'])
        diff=((oldbody-newbody)^upper).volume()+((newbody-oldbody)^upper).volume()
        assert abs(diff)<.001,(label,diff)
        assert len(newbody.decompose())==1,label
        assert len(a)==len(b),(label,len(a),len(b))
        for aa,bb in zip(a[1:],b[1:]):
            assert aa['settings'].get('extruder')==bb['settings'].get('extruder'),label
            error=float(cKDTree(aa['mesh'].vertices).query(bb['mesh'].vertices)[0].max())
            assert error<.0001,(label,error)
        rows.append(dict(part=label,visible_volume_difference_above_Z8_mm3=float(diff),color_modifier_geometry_and_assignments_preserved=True))
    save_json(OUT/'Independent-geometry-checks.json',dict(source_sha256=sha(ROOT/'Dara.3mf'),
        source_hammer_grid_vertices_checked=count,maximum_hammer_field_error_mm=max(errors),frame_checks=rows,
        flat_core_and_veneer_checks=flat_checks,constant_planar_glue_space_mm=SEAT_Z-CORE_BASE,
        scope='Digital geometry only; native toolpaths and physical samples are separate checks.'))
    print('Verified original hammer field and all 20 frame show surfaces / color modifiers.')


if __name__=='__main__':check()
