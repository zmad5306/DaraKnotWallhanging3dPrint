"""Regenerate all production carriers, patching only their editable mesh assets."""
import argparse,json,zipfile
import xml.etree.ElementTree as ET
import numpy as np
import shapely
from shapely import affinity,union_all
from shapely.geometry import Point,shape
from development_3mf import mesh_xml,tag,P,save_json,sha,z_rotation,common_m_rotation
from build_jointed_bambu_project import xml
from veneer_fin_carrier import fin_carrier
from develop_m_veneer import height_mesh,skin_bottom


def patch(project,replacements,normal):
    with zipfile.ZipFile(project) as z:files={n:z.read(n) for n in z.namelist()}
    before=dict(files);root=ET.fromstring(files['3D/3dmodel.model']);cfg=ET.fromstring(files['Metadata/model_settings.config'])
    changed=[]
    for oid,m in replacements.items():
        obj=root.find(tag('resources')).find(f"{tag('object')}[@id='{oid}']")
        components=list(obj.find(tag('components')));assert len(components)==1
        co=components[0];pid=co.get('objectid');path=co.get('{'+P+'}path').lstrip('/')
        child=ET.fromstring(files[path]);resources=child.find(tag('resources'))
        resources.remove(resources.find(f"{tag('object')}[@id='{pid}']"))
        mesh_xml(resources,int(pid),m,block_front=True,front_normal=normal)
        files[path]=xml(child);changed.append(path)
        cfg.find(f"object[@id='{oid}']/part[@id='{pid}']/mesh_stat").set('face_count',str(len(m.faces)))
    files['Metadata/model_settings.config']=xml(cfg)
    assert all(v==files[n] for n,v in before.items() if n not in changed+['Metadata/model_settings.config'])
    with zipfile.ZipFile(project,'w',zipfile.ZIP_DEFLATED) as z:
        for n,v in files.items():z.writestr(n,v)
    return changed


def a2l(selected=(1,2,3)):
    import build_a2l_project as b
    import plan_veneer_fins as planner
    plan=b.load_plan();path=b.OUT/'M-geometry-validation.json';report=json.loads(path.read_text())
    pre=z_rotation(90);rotation=common_m_rotation();replacements={}
    pp_path=b.OUT/'plate-plan.json';pp=json.loads(pp_path.read_text())
    hardware=union_all([Point(row[2]).buffer(7) for row in plan['screw_mounts']+plan['dowel_mounts']])
    for i,row in enumerate(report['skins'],1):
        if i not in selected:continue
        raw=b.cached(f'V{i}-raw');local=raw.copy();T=np.eye(4);T[:3,:3]=pre;local.apply_transform(T)
        region=affinity.rotate(shape(plan['skin_regions'][i-1]),90,origin=(0,0))
        excluded=union_all([Point(a['xy_mm']).buffer(7) for a in row['anchors']]).union(hardware)
        excluded=affinity.rotate(excluded,90,origin=(0,0))
        pose=np.array(row['assembly_to_printer']);pose[:3,:3]=rotation
        carried,evidence=fin_carrier(local,region,skin_bottom,pose,excluded,height_mesh,bed=(330,320),height=325,force_guard=True)
        old_sample=planner.SAMPLE;planner.SAMPLE=.75
        xy,weights,allowance=planner.area_samples(region)
        rows=[dict(contacts=np.array(r['contacts_xy_mm'])) for r in evidence['fins']]
        fine=planner.coverage(rows,xy,weights,allowance,shapely.distance(shapely.points(xy),shape(evidence['starter_contact_region'])))
        planner.SAMPLE=old_sample;limits=evidence['area_coverage']['trial_geometric_limits']
        assert fine['area_outside_distance_limit_mm2']<1e-6
        assert fine['maximum_area_per_bond_mm2']<=limits['maximum_rear_area_per_bond_mm2']+1e-6
        assert fine['maximum_tributary_width_mm']<=limits['maximum_tributary_width_mm']+1e-6
        evidence['independent_fine_grid']=fine;evidence['contact_coordinate_basis']='assembly rotated 90 degrees about Z before 55 degree lean'
        row['carrier']=evidence;b.cache(f'V{i}',carried)
        record=next(r for r in pp['records'] if r['plate']==i+14)
        replacements[str(record['object_id'])]=carried
        record['body_bounds_mm']=carried.bounds.tolist()
        print(f'A2L V{i}: {evidence["fin_count"]} fins, {evidence["starter_rib_count"]} separate ribs; all cutter windows clear',flush=True)
    changed=patch(b.EDIT,replacements,np.array(plan['veneer_rotation'])[:,2])
    pp['editable_sha256']=sha(b.EDIT);save_json(pp_path,pp);save_json(path,report)
    save_json(b.OUT/'veneer-carrier-update.json',dict(revision='clean-trim-production-v2',changed_child_assets=changed,
        only_veneer_children_and_face_counts_changed=True,saved_poses_materials_and_other_geometry_preserved=True,
        editable_sha256=sha(b.EDIT),all_veneers_checked=sum(r['carrier'].get('revision')=='clean-trim-production-v2' for r in report['skins']),physical_confirmation_pending=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('family',choices=['a2l']);p.add_argument('--veneers',type=int,nargs='+',default=[1,2,3]);a=p.parse_args();a2l(a.veneers)
