"""Independent release-to-candidate checks for the development branch."""
import json
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import Point, box
from shapely import union_all

from development_3mf import *
from develop_m_veneer import texture, prism, locate, SKIN_JOINTS
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
        scope='Digital geometry only; native toolpaths and physical samples are separate checks.'))
    print('Verified original hammer field and all 20 frame show surfaces / color modifiers.')


if __name__=='__main__':check()
