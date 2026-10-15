"""Remove the distance-field crease from cover show faces; keep their seats.

The one-cover project is a physical confirmation sample, not proof that every
mark in the previous print or slicer screenshot had the same cause.
"""
import argparse
import hashlib
import json
import math
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import prepare_hammered_bands as b
from prepare_cover_edge_test import shape as original_shape, surface_error, underside_distance
from prepare_cover_precision_test import face_paths
from prepare_y_stable_dara import motion_audit
from integrate_hammered_dara import TARGETS

WORK=b.ROOT/'.work/cover-crown'
REVIEW=b.ROOT/'working/review/cover-crown'
BASE=b.ROOT/'Dara-Cover-Edge-Test.3mf'
TARGET=b.ROOT/'Dara-Cover-Smooth-Crown-Test.3mf'


def shape(index):
    region,floor,_=original_shape(index)
    outline=b.layout()[1];crown=b.smooth_cover_crown(outline,region)
    def top(xy):
        edge=b.shapely.distance(b.shapely.points(xy),region.boundary)
        return 10.5+crown(xy)-b.SEAT_DEPTH+b.GLUE_GAP+b.THICKNESS-.25*(1-b.np.clip(edge/.25,0,1))
    return region,floor,top


def geometry():
    WORK.mkdir(parents=True,exist_ok=True);REVIEW.mkdir(parents=True,exist_ok=True)
    rows=[]
    for i in range(1,6):
        region,floor,top=shape(i)
        body=b.boolean([b.band_envelope(region,top),b.envelope(floor,region.bounds,.25)],'difference')
        saved=b.np.load(b.ROOT/f'.work/cover-edge/B{i}.npz')
        old=b.trimesh.Trimesh(saved['vertices'],saved['faces'],process=False)
        assert body.is_volume and body.is_watertight and body.body_count==1
        err=surface_error(body,top);assert err['max_mm']<=.001001
        underside=underside_distance(old,body)
        xy=body.triangles_center[body.face_normals[:,2]>.01,:2]
        original_top=original_shape(i)[2]
        change=top(xy)-original_top(xy)
        thick=top(xy)-floor(xy)
        assert thick.min()>.9 and abs(change).max()<.04
        row=dict(name=f'B{i}',triangles=len(body.faces),volume_mm3=float(body.volume),
                 top_change_mm=[float(change.min()),float(change.max())],
                 min_sampled_thickness_mm=float(thick.min()),surface_error=err,underside=underside)
        rows.append(row);b.np.savez_compressed(WORK/f'B{i}.npz',vertices=body.vertices,faces=body.faces)
        print(json.dumps(row),flush=True)
    (REVIEW/'geometry.json').write_text(json.dumps(rows,indent=2)+'\n')


def stage():
    source=b.read_zip(BASE);settings=json.loads(source['Metadata/project_settings.config'])
    assert settings['enable_arc_fitting']=='0' and settings['resolution']=='0.001'
    settings['print_settings_id']='Dara B1 - smooth crown - physical confirmation pending'
    a=b.np.load(WORK/'B1.npz');body=b.trimesh.Trimesh(a['vertices'],a['faces'],process=False)
    prior=json.loads((b.ROOT/'.work/cover-edge/stage.json').read_text())
    t=b.centered(body,b.np.array(prior['orientation']['build_transform']),[128,128])
    files={k:source[k] for k in ['[Content_Types].xml','_rels/.rels']}
    root=b.model();del root.attrib['xmlns:p']
    for k,v in [('Application','BambuStudio-02.08.02.61'),('BambuStudio:3mfVersion','1'),('Title','B1 smooth crown')]:
        ET.SubElement(root,b.tag('metadata'),name=k).text=v
    resources=ET.SubElement(root,b.tag('resources'));build=ET.SubElement(root,b.tag('build'),attrib={'{'+b.P+'}UUID':b.uid()})
    config=ET.Element('config');relations=ET.Element('Relationships',xmlns=b.R)
    orientation=b.add_object(files,resources,build,config,relations,'B1',body,t,1000,[],[])
    original=ET.fromstring(source['Metadata/model_settings.config']).find('object')
    cfg=config.find('object')
    for node in list(cfg.findall('metadata')):cfg.remove(node)
    for key,value in b.props(original).items():
        if key is not None:b.meta(cfg,key,value)
    b.setmeta(cfg,'name','B1 - smooth crown; preserved glue seat')
    plate=ET.SubElement(config,'plate')
    for key,value in [('plater_id',1),('plater_name','B1 SMOOTH CROWN'),('locked','false'),('filament_map_mode','Auto For Flush'),('filament_maps','1 1 1 1'),('filament_volume_maps','0 0 0 0')]:b.meta(plate,key,value)
    inst=ET.SubElement(plate,'model_instance')
    for key,value in [('object_id',1000),('instance_id',0),('identify_id',1)]:b.meta(inst,key,value)
    files.update({'3D/3dmodel.model':b.xml(root),'3D/_rels/3dmodel.model.rels':b.xml(relations),
                  'Metadata/model_settings.config':b.xml(config),'Metadata/project_settings.config':json.dumps(settings,indent=2).encode()})
    b.write_zip(WORK/'staged.3mf',files)
    report=dict(orientation=orientation,baseline_sha256=b.sha(BASE),
                preserved={str(p.relative_to(b.ROOT)):b.sha(p) for p in [BASE,*TARGETS]})
    (WORK/'stage.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Staged smooth crown with original process, underside and orientation.',flush=True)


def slice_native():
    out=WORK/'slice';out.mkdir(exist_ok=True)
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    with (out/'cli.log').open('w') as log:
        result=subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf','--outputdir',str(out),str(WORK/'staged.3mf')],
                              cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode==0,result.returncode
    print('Native slice complete.',flush=True)


def verify():
    manifest=json.loads((WORK/'stage.json').read_text());t=b.np.array(manifest['orientation']['build_transform'])
    assert abs(t[1,2])<1e-8 and abs(t[2,2]-math.cos(math.radians(55)))<1e-8
    staged=b.read_zip(WORK/'staged.3mf');files=b.read_zip(WORK/'slice/sliced.3mf')
    assert json.loads((WORK/'slice/result.json').read_text())['return_code']==0
    expected=json.loads(staged['Metadata/project_settings.config']);actual=json.loads(files['Metadata/project_settings.config'])
    assert all(actual.get(k)==v for k,v in expected.items())
    before=b.model_entries(staged);after=b.model_entries(files)
    assert set(before)==set(after)=={'B1'} and len(after['B1'])==1
    a=before['B1'][0];c=after['B1'][0];mesh=c['mesh']
    assert mesh.is_volume and mesh.is_watertight and mesh.body_count==1
    error=max(b.cKDTree(mesh.vertices).query(a['mesh'].vertices)[0].max(),b.cKDTree(a['mesh'].vertices).query(mesh.vertices)[0].max())
    assert error<.0002
    assert all(int((a['paint']==k).sum())==int((c['paint']==k).sum()) for k in [4,8])
    info=ET.fromstring(files['Metadata/slice_info.config']);assert len(info.findall('plate'))==1
    plate=info.find('plate');stats=b.props(plate)
    assert stats['outside']=='false' and stats['pause_count']=='0'
    assert {f.get('id') for f in plate.findall('filament')}=={'1'}
    assert all(w.get('msg')=='not_support_traditional_timelapse' for w in plate.findall('warning'))
    b.setmeta(plate,'printer_model_id','N2S')
    first=float(stats.get('first_layer_time',0))
    if not math.isfinite(first) or not 0<=first<=float(stats['prediction']):plate.remove(plate.find("metadata[@key='first_layer_time']"))
    gcode=files['Metadata/plate_1.gcode'];text=gcode.decode()
    assert hashlib.md5(gcode).hexdigest()==files['Metadata/plate_1.gcode.md5'].decode().strip().lower()
    audit=b.scan_gcode(text);zs=audit.pop('model_extrusion_z_by_filament_mm')
    assert set(zs)=={'1'} and .1999<=min(zs['1'])<=max(zs['1'])<250
    assert audit['conservative_bed_edge_clearance_mm']>6
    assert all(audit['features'].get(k,0)>0 for k in ['Outer wall','Support','Support interface'])
    paths,_=b.support_paths(text);base=paths['Support'][b.np.max(paths['Support'][:,:,2],axis=1)<=.201]
    assert len(base)>0
    region,floor,_=shape(1)
    local=b.trimesh.transform_points(paths['Support interface'].mean(axis=1),b.np.linalg.inv(t))
    inside=b.shapely.contains(region.buffer(-.6),b.shapely.points(local[:,:2]));assert inside.any()
    delta=float((local[inside,2]-floor(local[inside,:2])).max());assert delta<.12
    motion=motion_audit(text)
    assert 'M201 X1000 Y1000 Z1500 E5000' in motion['axis_limit_commands']
    assert 'M203 X150 Y150 Z30 E30' in motion['axis_limit_commands']
    _,tangents=face_paths(text,t);assert tangents['model_extrusion_arcs']==0
    for path,digest in manifest['preserved'].items():assert b.sha(b.ROOT/path)==digest,path
    files['Metadata/slice_info.config']=b.xml(info);b.write_zip(TARGET,files)
    report=dict(project_sha256=b.sha(TARGET),source=manifest,mesh_roundtrip_error_mm=float(error),
                weight_g=float(stats['weight']),seconds=int(stats['prediction']),gcode_sha256=hashlib.sha256(gcode).hexdigest(),
                support_base_segments=len(base),max_interface_above_underside_mm=delta,motion=motion,path_audit=audit,
                tangent_summary={k:v for k,v in tangents.items() if k!='joins'},physical_print_pending=True,
                conclusion='C2 show-face field replaces the nearest-edge crown crease. Preserved underside; physical finish unverified.')
    (REVIEW/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Verified',TARGET.name,report['weight_g'],'g',report['seconds'],'seconds',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['geometry','stage','slice','verify']);a=p.parse_args()
    {'geometry':geometry,'stage':stage,'slice':slice_native,'verify':verify}[a.action]()
