"""Repair undersampled cover bevels and isolate B1 for optional physical testing.

This repairs a measured geometric defect at the rim. It does NOT establish
the cause or cure of the separate transverse scar in Zach's physical print.
"""
import argparse
import hashlib
import json
import math
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import prepare_hammered_bands as b
from integrate_hammered_dara import TARGETS
from prepare_y_stable_dara import motion_audit

WORK=b.ROOT/'.work/cover-edge'
REVIEW=b.ROOT/'working/review/cover-edge'
BASE=b.ROOT/'Dara-Cover-Only-Test.3mf'
TARGET=b.ROOT/'Dara-Cover-Edge-Test.3mf'


def shape(index):
    _,outline,joints,_=b.layout();j=joints[index-1]
    region=b.locate(b.rect(-b.WIDTH/2,-j[4],b.WIDTH/2,j[4]),j[2],j[3]).intersection(outline.buffer(-.15))
    def floor(xy):return 10.5+b.crown(outline,xy)-b.SEAT_DEPTH+b.GLUE_GAP
    def top(xy):return floor(xy)+b.THICKNESS-.25*(1-b.np.clip(b.shapely.distance(b.shapely.points(xy),region.boundary)/.25,0,1))
    return region,floor,top


def surface_error(mesh,evaluate):
    tri=mesh.triangles[mesh.face_normals[:,2]>.01]
    probes=b.np.concatenate([tri.mean(axis=1)[:,None,:],(tri+b.np.roll(tri,-1,axis=1))/2],axis=1).reshape(-1,3)
    errors=b.np.abs(probes[:,2]-evaluate(probes[:,:2]))
    return dict(sample_count=len(probes),max_mm=float(errors.max()),p99_mm=float(b.np.percentile(errors,99)))


def underside_distance(a,c):
    """Upper bound on surface distance, with full search for ambiguous samples.

    Vertex-to-vertex comparison is invalid when the same plane is retriangulated.
    Compare both vertices and face centers to actual underside triangles.
    """
    worst=0.;count=0
    for source,target in [(a,c),(c,a)]:
        st=source.triangles[source.face_normals[:,2]<-.01]
        tt=target.triangles[target.face_normals[:,2]<-.01]
        points=b.np.concatenate([b.np.unique(st.reshape(-1,3),axis=0),st.mean(axis=1)])
        _,near=b.cKDTree(tt.mean(axis=1)).query(points,k=16)
        repeated=b.np.repeat(points,16,axis=0)
        closest=b.trimesh.triangles.closest_point(tt[near].reshape(-1,3,3),repeated)
        distance=b.np.linalg.norm(closest-repeated,axis=1).reshape(-1,16).min(axis=1)
        for i in b.np.where(distance>.00015)[0]:
            repeated=b.np.broadcast_to(points[i],(len(tt),3))
            closest=b.trimesh.triangles.closest_point(tt,repeated)
            distance[i]=b.np.linalg.norm(closest-repeated,axis=1).min()
        worst=max(worst,float(distance.max()));count+=len(points)
    assert worst<.0002,worst
    return dict(sample_count=count,max_distance_mm=worst)


def geometry():
    WORK.mkdir(parents=True,exist_ok=True);REVIEW.mkdir(parents=True,exist_ok=True)
    rows=[]
    for i in range(1,6):
        region,floor,top=shape(i)
        seat=b.envelope(floor,region.bounds,.25)
        old=b.boolean([b.boolean([b.envelope(top,region.bounds,.25),b.prism(region,8,6.6)],'intersection'),seat],'difference')
        new=b.boolean([b.band_envelope(region,top),seat],'difference')
        assert new.is_volume and new.is_watertight and new.body_count==1
        errors=surface_error(new,top);assert errors['max_mm']<=.001001
        row=dict(name=f'B{i}',original=surface_error(old,top),corrected=errors,
                 underside=underside_distance(old,new),triangles=len(new.faces),volume_mm3=float(new.volume))
        rows.append(row)
        b.np.savez_compressed(WORK/f'B{i}.npz',vertices=new.vertices,faces=new.faces)
        if i==1:render_geometry(old,new)
        print(json.dumps(row),flush=True)
    (REVIEW/'geometry.json').write_text(json.dumps(rows,indent=2)+'\n')


def render_geometry(old,new):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    j=b.layout()[2][0];local=b.rotation(-j[3]);local[:2,3]=-local[:2,:2]@b.np.array(j[2])
    fig,axes=plt.subplots(2,1,figsize=(12,4),facecolor='#f4f1eb')
    light=b.np.array([-.8,.1,.6]);light/=b.np.linalg.norm(light)
    for ax,m,label in zip(axes,[old,new],['Original: bevel sampled before clipping','Corrected: bevel boundaries included in the mesh']):
        m=m.copy();m.apply_transform(local);sel=m.face_normals[:,2]>.01
        tri=m.triangles[sel];shade=.25+.75*b.np.maximum(m.face_normals[sel]@light,0)
        ax.add_collection(PolyCollection(tri[:,:,[1,0]],facecolors=b.np.array([.89,.49,.23])[None,:]*shade[:,None],edgecolors='none',antialiaseds=False))
        ax.set(xlim=(-16,10),ylim=(4.8,6.05),aspect='equal');ax.set_axis_off();ax.set_title(label,fontsize=11)
    fig.suptitle('B1 rim detail — shading of actual model triangles',fontsize=14)
    fig.text(.5,.04,'Same nominal 0.25 mm bevel and seating surface. This illustrates geometry, not a predicted print finish.',ha='center',fontsize=9)
    fig.subplots_adjust(top=.78,bottom=.16,hspace=.8);fig.savefig(REVIEW/'bevel-comparison.png',dpi=160);plt.close(fig)


def stage():
    a=b.np.load(WORK/'B1.npz');body=b.trimesh.Trimesh(a['vertices'],a['faces'],process=False)
    source=b.read_zip(BASE);settings=json.loads(source['Metadata/project_settings.config'])
    assert settings['enable_arc_fitting']=='0' and settings['resolution']=='0.001'
    settings['print_settings_id']='Dara B1 - repaired bevel - physical scar unresolved'
    report=json.loads((b.ROOT/'working/review/y-stable-dara/test-validation.json').read_text())
    assert b.sha(b.TEST)==report['project_sha256']
    orientation=next(o for o in report['orientation'] if o['name']=='B1')
    t=b.centered(body,b.np.array(orientation['build_transform']),[128,128])
    assert abs(t[1,2])<1e-8 and abs(t[2,2]-math.cos(math.radians(55)))<1e-8
    files={k:source[k] for k in ['[Content_Types].xml','_rels/.rels']}
    root=b.model();del root.attrib['xmlns:p']
    for k,v in [('Application','BambuStudio-02.08.02.61'),('BambuStudio:3mfVersion','1'),('Title','B1 cover - bevel repair')]:
        ET.SubElement(root,b.tag('metadata'),name=k).text=v
    resources=ET.SubElement(root,b.tag('resources'));build=ET.SubElement(root,b.tag('build'),attrib={'{'+b.P+'}UUID':b.uid()})
    config=ET.Element('config');relations=ET.Element('Relationships',xmlns=b.R)
    row=b.add_object(files,resources,build,config,relations,'B1',body,t,1000,[],[])
    original=ET.fromstring(source['Metadata/model_settings.config']).find('object')
    # Retain the prior object's overrides, replacing only geometry and its paint.
    cfg=config.find('object')
    for node in list(cfg.findall('metadata')):cfg.remove(node)
    for key,value in b.props(original).items():
        if key is not None:b.meta(cfg,key,value)
    b.setmeta(cfg,'name','B1 - repaired bevel; middle scar unconfirmed')
    plate=ET.SubElement(config,'plate')
    for key,value in [('plater_id',1),('plater_name','B1 bevel repair'),('locked','false'),('filament_map_mode','Auto For Flush'),('filament_maps','1 1 1 1'),('filament_volume_maps','0 0 0 0')]:b.meta(plate,key,value)
    inst=ET.SubElement(plate,'model_instance')
    for key,value in [('object_id',1000),('instance_id',0),('identify_id',1)]:b.meta(inst,key,value)
    files.update({'3D/3dmodel.model':b.xml(root),'3D/_rels/3dmodel.model.rels':b.xml(relations),
                  'Metadata/model_settings.config':b.xml(config),'Metadata/project_settings.config':json.dumps(settings,indent=2).encode()})
    b.write_zip(WORK/'staged.3mf',files)
    manifest=dict(orientation=row,baseline_sha256=b.sha(BASE),
                  preserved={str(p.relative_to(b.ROOT)):b.sha(p) for p in [*TARGETS,b.TARGET,b.TEST,BASE]})
    (WORK/'stage.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Staged corrected B1; prior precision-test process and object overrides retained.')


def slice_native():
    out=WORK/'slice';out.mkdir(exist_ok=True)
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    with (out/'cli.log').open('w') as log:
        result=subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf','--outputdir',str(out),str(WORK/'staged.3mf')],
                              cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode==0,result.returncode
    print('Native Bambu slice complete.')


def verify():
    out=WORK/'slice';assert json.loads((out/'result.json').read_text())['return_code']==0
    manifest=json.loads((WORK/'stage.json').read_text());t=b.np.array(manifest['orientation']['build_transform'])
    staged=b.read_zip(WORK/'staged.3mf');files=b.read_zip(out/'sliced.3mf')
    expected=json.loads(staged['Metadata/project_settings.config']);actual=json.loads(files['Metadata/project_settings.config'])
    assert all(actual.get(k)==v for k,v in expected.items())
    assert set(actual)-set(expected)<={'different_settings_to_system','inherits_group','filament_map_2'}
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
    if not math.isfinite(first) or not 0<=first<=float(stats['prediction']):
        plate.remove(plate.find("metadata[@key='first_layer_time']"))
    gcode=files['Metadata/plate_1.gcode'];text=gcode.decode()
    assert hashlib.md5(gcode).hexdigest()==files['Metadata/plate_1.gcode.md5'].decode().strip().lower()
    assert not re.search(r'^\s*(?:M400\s+U1|M0(?:\s|$)|M1(?:\s|$)|M25(?:\s|$))',text,re.M)
    audit=b.scan_gcode(text);zs=audit.pop('model_extrusion_z_by_filament_mm')
    assert set(zs)=={'1'} and .1999<=min(zs['1'])<=max(zs['1'])<250
    assert audit['conservative_bed_edge_clearance_mm']>6
    assert all(audit['features'].get(k,0)>0 for k in ['Outer wall','Support','Support interface'])
    assert not audit['features'].get('Ironing',0)
    paths,_=b.support_paths(text);base=paths['Support'][b.np.max(paths['Support'][:,:,2],axis=1)<=.201]
    assert len(base)>0
    local=b.trimesh.transform_points(paths['Support interface'].mean(axis=1),b.np.linalg.inv(t))
    region,floor,_=shape(1);inside=b.shapely.contains(region.buffer(-.6),b.shapely.points(local[:,:2]))
    assert inside.any();delta=float((local[inside,2]-floor(local[inside,:2])).max());assert delta<.12
    motion=motion_audit(text)
    assert 'M201 X1000 Y1000 Z1500 E5000' in motion['axis_limit_commands']
    assert 'M203 X150 Y150 Z30 E30' in motion['axis_limit_commands']
    for path,digest in manifest['preserved'].items():assert b.sha(b.ROOT/path)==digest,path
    files['Metadata/slice_info.config']=b.xml(info);b.write_zip(TARGET,files)
    report=dict(project_sha256=b.sha(TARGET),source=manifest,mesh_roundtrip_error_mm=float(error),
                weight_g=float(stats['weight']),seconds=int(stats['prediction']),gcode_sha256=hashlib.sha256(gcode).hexdigest(),
                support_base_segments=len(base),max_interface_above_underside_mm=delta,motion=motion,path_audit=audit,
                physical_print_pending=True,complete_project_changed=False,
                conclusion='Bevel sampling defect repaired. Separate physical transverse scar remains unexplained; no claim of a cure.')
    (REVIEW/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Published',TARGET.name,report['weight_g'],'g',report['seconds'],'seconds')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['geometry','stage','slice','verify'])
    action=parser.parse_args().action
    {'geometry':geometry,'stage':stage,'slice':slice_native,'verify':verify}[action]()
