"""Promote the checked bevel repair to plate 31 of the complete Dara project.

Preserve all other objects, placements, settings and native plate assets.
The physical middle-scar result remains pending independently of this repair.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

import prepare_hammered_bands as b
import prepare_cover_edge_test as edge
from integrate_hammered_dara import TARGETS,PACKAGE,selected_entries,plate_offset,digest
from prepare_y_stable_dara import motion_audit

WORK=b.ROOT/'.work/cover-edge-production'
REVIEW=b.ROOT/'working/review/cover-edge-production'
NAMES={f'Band{i}' for i in range(1,6)}
META=('3D/3dmodel.model','Metadata/model_settings.config','Metadata/slice_info.config','Metadata/filament_sequence.json')


def plate_asset(path):
    match=re.match(r'Metadata/(?:plate_|plate_no_light_|top_|pick_)(\d+)[_.]',path)
    return bool(match and int(match[1])==31)


def stage():
    WORK.mkdir(parents=True,exist_ok=True);REVIEW.mkdir(parents=True,exist_ok=True)
    prior=json.loads((PACKAGE/'y-stability-validation.json').read_text())
    assert b.sha(TARGETS[0])==b.sha(TARGETS[1])==prior['project_sha256'],'This migration expects the Y-stable release.'
    shutil.copy2(TARGETS[0],WORK/'baseline.3mf')
    files=b.read_zip(TARGETS[0]);root=ET.fromstring(files[META[0]]);cfg=ET.fromstring(files[META[1]])
    entries=selected_entries(files,NAMES);assert set(entries)==NAMES
    resources=root.find(b.tag('resources'));build=root.find(b.tag('build'))
    configs={b.props(o)['name'].split(' - ')[0]:o for o in cfg.findall('object')}
    orientation={o['name']:o for o in prior['orientation']};rows=[]
    for i in range(1,6):
        name=f'Band{i}';co=configs[name];oid=co.get('id')
        assert len(entries[name])==1
        reference=entries[name][0]['mesh']
        oldt=b.np.array(orientation[name]['build_transform']);world=oldt.copy();world[:2,3]+=plate_offset(31,6)
        old=reference.copy();old.apply_transform(b.np.linalg.inv(world))
        data=b.np.load(edge.WORK/f'B{i}.npz');body=b.trimesh.Trimesh(data['vertices'],data['faces'],process=False)
        region,floor,top=edge.shape(i)
        assert body.is_volume and body.is_watertight and body.body_count==1
        errors=edge.surface_error(body,top);assert errors['max_mm']<=.001001
        # Native rounding can flip normals on tiny, nearly degenerate facets.
        # First match the current solid to its original mesh, then compare the
        # repaired seat against that unrounded original surface.
        original=b.boolean([b.boolean([b.envelope(top,region.bounds,.25),b.prism(region,8,6.6)],'intersection'),b.envelope(floor,region.bounds,.25)],'difference')
        source_error=max(b.cKDTree(original.vertices).query(old.vertices)[0].max(),b.cKDTree(old.vertices).query(original.vertices)[0].max())
        assert source_error<.0002,(name,source_error)
        underside=edge.underside_distance(original,body)
        center=reference.bounds.mean(axis=0)[:2]-plate_offset(31,6)
        t=b.centered(body,oldt,center)
        assert abs(t[1,2])<1e-8 and abs(t[2,2]-math.cos(math.radians(55)))<1e-8
        obj=resources.find(f"{b.tag('object')}[@id='{oid}']");comps=list(obj.find(b.tag('components')));assert len(comps)==1
        comp=comps[0];path=comp.get('{'+b.P+'}path').lstrip('/');mid=comp.get('objectid')
        child=b.model();cr=ET.SubElement(child,b.tag('resources'));b.mesh_object(cr,mid,body)
        normal=body.face_normals;placed=normal@t[:3,:3].T;front=normal[:,2]>-.01
        enforce=(placed[:,2]<-.1)&~front;block=front
        triangles=cr.find(b.tag('object')).find(b.tag('mesh')).find(b.tag('triangles'))
        for idx in b.np.where(enforce|block)[0]:triangles[idx].set('paint_supports','8' if block[idx] else '4')
        files[path]=b.xml(child);comp.set('transform',b.IDENTITY)
        world=t.copy();world[:2,3]+=plate_offset(31,6)
        item=build.find(f"{b.tag('item')}[@objectid='{oid}']")
        item.set('transform',' '.join(f'{v:.12g}' for v in world[:3,:].T.ravel()))
        for md in co.findall('metadata'):
            if md.get('face_count') is not None:md.set('face_count',str(len(body.faces)))
        part=co.find('part');assert part.get('id')==mid
        for md in list(part.findall('metadata')):
            if md.get('key','').startswith('source_'):part.remove(md)
        b.setmeta(part,'matrix','1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1')
        stat=part.find('mesh_stat');stat.set('face_count',str(len(body.faces)))
        for key in ['edges_fixed','degenerate_facets','facets_removed','facets_reversed','backwards_edges']:stat.set(key,'0')
        assemble=cfg.find('assemble')
        if assemble is not None:
            for a in list(assemble):
                if a.get('object_id')==oid:assemble.remove(a)
        rows.append(dict(name=name,object_id=oid,mesh_path=path,build_transform=t.tolist(),
                         triangles=len(body.faces),surface_error=errors,underside=underside,source_roundtrip_error_mm=float(source_error),
                         enforced_facets=int(enforce.sum()),blocked_facets=int(block.sum())))
    files[META[0]]=b.xml(root);files[META[1]]=b.xml(cfg)
    b.write_zip(WORK/'staged.3mf',files)
    manifest=dict(baseline_sha256=b.sha(TARGETS[0]),objects=rows,settings_changed=False,
                  geometry_source_report_sha256=b.sha(edge.REVIEW/'geometry.json'),
                  test_sha256=b.sha(edge.TARGET),prior_report=prior)
    (WORK/'stage.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Staged five repaired bands on plate 31; existing settings retained.',flush=True)


def slice_native():
    out=WORK/'slice';out.mkdir(exist_ok=True);exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    with (out/'cli.log').open('w') as log:
        r=subprocess.run([str(exe),'--slice','31','--export-3mf','sliced.3mf','--outputdir',str(out),str(WORK/'staged.3mf')],
                         cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    assert r.returncode==0,r.returncode
    result=json.loads((out/'result.json').read_text());assert result['return_code']==0 and result['plate_index']==31
    print('Plate 31 sliced with regenerated native supports.',flush=True)


def verify():
    manifest=json.loads((WORK/'stage.json').read_text());original=b.read_zip(WORK/'baseline.3mf')
    assert b.sha(WORK/'baseline.3mf')==manifest['baseline_sha256']
    assert b.sha(edge.TARGET)==manifest['test_sha256']
    files=b.read_zip(WORK/'staged.3mf');sliced=b.read_zip(WORK/'slice/sliced.3mf')
    expected=selected_entries(files,NAMES);actual=b.model_entries(sliced);assert set(actual)==NAMES
    es=json.loads(files['Metadata/project_settings.config']);ns=json.loads(sliced['Metadata/project_settings.config'])
    assert all(ns.get(k)==v for k,v in es.items())
    assert set(ns)-set(es)<={'different_settings_to_system','inherits_group','filament_map_2'}
    cfg=ET.fromstring(files[META[1]]);sc=ET.fromstring(sliced[META[1]]);scfg={b.props(o)['name'].split(' - ')[0]:o for o in sc.findall('object')}
    mesh_checks=[]
    for row in manifest['objects']:
        name=row['name'];a=expected[name][0];c=actual[name][0];m=c['mesh']
        assert len(actual[name])==1 and m.is_volume and m.is_watertight and m.body_count==1
        error=max(b.cKDTree(m.vertices).query(a['mesh'].vertices)[0].max(),b.cKDTree(a['mesh'].vertices).query(m.vertices)[0].max())
        assert error<.0002,(name,error)
        assert all(int((a['paint']==k).sum())==int((c['paint']==k).sum()) for k in [4,8])
        co=cfg.find(f"object[@id='{row['object_id']}']")
        for k,v in b.props(co).items():
            if k is not None:assert b.props(scfg[name])[k]==v,(name,k)
        assert b.props(scfg[name])['extruder']=='3'
        mesh_checks.append(dict(name=name,roundtrip_error_mm=float(error)))
    si=ET.fromstring(sliced[META[2]]);assert len(si.findall('plate'))==1
    stat=si.find('plate');stats=b.props(stat)
    assert stats['index']=='31' and stats['outside']=='false' and stats['pause_count']=='0'
    assert {f.get('id') for f in stat.findall('filament')}=={'3'}
    assert all(w.get('msg')=='not_support_traditional_timelapse' for w in stat.findall('warning'))
    b.setmeta(stat,'printer_model_id','N2S');first=float(stats.get('first_layer_time',0))
    if not math.isfinite(first) or not 0<=first<=float(stats['prediction']):stat.remove(stat.find("metadata[@key='first_layer_time']"))
    gcode=sliced['Metadata/plate_31.gcode'];text=gcode.decode()
    assert hashlib.md5(gcode).hexdigest()==sliced['Metadata/plate_31.gcode.md5'].decode().strip().lower()
    assert not re.search(r'^\s*(?:M400\s+U1|M0(?:\s|$)|M1(?:\s|$)|M25(?:\s|$))',text,re.M)
    audit=b.scan_gcode(text);zs=audit.pop('model_extrusion_z_by_filament_mm');assert set(zs)=={'3'}
    assert .1999<=min(zs['3'])<=max(zs['3'])<250 and audit['conservative_bed_edge_clearance_mm']>6
    assert all(audit['features'].get(k,0)>0 for k in ['Outer wall','Support','Support interface'])
    paths,_=b.support_paths(text);centers=paths['Support interface'].mean(axis=1);support_checks=[]
    for i,row in enumerate(manifest['objects'],1):
        name=row['name'];body=expected[name][0]['mesh'].copy();body.apply_translation([*-plate_offset(31,6),0])
        near=b.np.all(centers>=body.bounds[0]-2,axis=1)&b.np.all(centers<=body.bounds[1]+2,axis=1)
        local=b.trimesh.transform_points(centers[near],b.np.linalg.inv(row['build_transform']))
        region,floor,_=edge.shape(i);inside=b.shapely.contains(region.buffer(-.6),b.shapely.points(local[:,:2]))
        assert inside.any();delta=float((local[inside,2]-floor(local[inside,:2])).max());assert delta<.12,(name,delta)
        bases=paths['Support'][b.np.max(paths['Support'][:,:,2],axis=1)<=.201].mean(axis=1)
        near_base=b.np.all(bases[:,:2]>=body.bounds[0,:2]-15,axis=1)&b.np.all(bases[:,:2]<=body.bounds[1,:2]+15,axis=1)
        assert near_base.any()
        support_checks.append(dict(name=name,interior_interface_points=int(inside.sum()),max_interface_above_underside_mm=delta,nearby_base_segments=int(near_base.sum())))
    motion=motion_audit(text)
    assert 'M201 X1000 Y1000 Z1500 E5000' in motion['axis_limit_commands']
    assert 'M203 X150 Y150 Z30 E30' in motion['axis_limit_commands']
    p=next(p for p in cfg.findall('plate') if b.props(p)['plater_id']=='31')
    sp=next(p for p in sc.findall('plate') if b.props(p)['plater_id']=='31')
    for path in list(files):
        if plate_asset(path):del files[path]
    for path,data in sliced.items():
        if plate_asset(path):files[path]=data
    for md in sp.findall('metadata'):
        key,path=md.get('key'),md.get('value')
        if key and key.endswith('_file') and path:b.setmeta(p,key,path);files[path]=sliced[path]
    info=ET.fromstring(files[META[2]]);info.remove(next(p for p in info.findall('plate') if b.props(p)['index']=='31'));info.append(stat)
    info[:]=info.findall('header')+sorted(info.findall('plate'),key=lambda p:int(b.props(p)['index']))
    sequences=json.loads(files[META[3]]);sequences['plate_31']=json.loads(sliced[META[3]])['plate_31'];assert sequences['plate_31']['sequence']==[3]
    files.update({META[1]:b.xml(cfg),META[2]:b.xml(info),META[3]:json.dumps(sequences).encode()})
    # Every other package asset is byte-identical. Also compare unaffected XML nodes.
    allowed=set(META)|{r['mesh_path'] for r in manifest['objects']}
    for path in set(original)|set(files):
        if path not in allowed and not plate_asset(path):assert original.get(path)==files.get(path),path
    oldcfg=ET.fromstring(original[META[1]]);oldroot=ET.fromstring(original[META[0]]);root=ET.fromstring(files[META[0]])
    changedids={r['object_id'] for r in manifest['objects']}
    for node in oldcfg.findall('object'):
        if node.get('id') not in changedids:assert b.xml(node)==b.xml(cfg.find(f"object[@id='{node.get('id')}']"))
    for oldparent,newparent in [(oldroot.find(b.tag('resources')),root.find(b.tag('resources'))),(oldroot.find(b.tag('build')),root.find(b.tag('build')))]:
        for a,c in zip(oldparent,newparent):
            if a.get('id',a.get('objectid')) not in changedids:assert b.xml(a)==b.xml(c)
    for a in oldcfg.findall('plate'):
        n=b.props(a)['plater_id']
        if n!='31':assert b.xml(a)==b.xml(next(p for p in cfg.findall('plate') if b.props(p)['plater_id']==n))
    assert len(cfg.findall('plate'))==len(info.findall('plate'))==32
    assert len(cfg.findall('object'))==47 and len(root.find(b.tag('build')))==78
    unchanged=[dict(plate=n,gcode_sha256=digest(files[f'Metadata/plate_{n}.gcode'])) for n in range(1,33) if n!=31]
    totals=[dict(plate=int(b.props(p)['index']),weight_g=float(b.props(p)['weight']),seconds=int(b.props(p)['prediction'])) for p in info.findall('plate')]
    candidate=WORK/'complete.3mf';b.write_zip(candidate,files)
    report=dict(project_sha256=b.sha(candidate),baseline_sha256=manifest['baseline_sha256'],plates=32,objects=47,instances=78,
                changed_plates=[dict(plate=31,gcode_sha256=digest(gcode),weight_g=float(stats['weight']),seconds=int(stats['prediction']),path_audit=audit,motion=motion,support_checks=support_checks)],
                unchanged_native_plates=unchanged,geometry_checks=manifest['objects'],mesh_checks=mesh_checks,
                settings_changed=False,precision_settings={k:es[k] for k in ['enable_arc_fitting','resolution']},
                total_weight_g=sum(r['weight_g'] for r in totals),total_seconds=sum(r['seconds'] for r in totals),all_plate_estimates=totals,
                physical_test_pending=True,scope='User-authorized promotion of all five repaired bevel meshes. Middle scar remains unconfirmed; existing production process retained.')
    (REVIEW/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Verified',stats['weight'],'g,',stats['prediction'],'seconds; all 31 other plates preserved.',flush=True)


def publish():
    report=json.loads((REVIEW/'validation.json').read_text());source=WORK/'complete.3mf'
    assert b.sha(source)==report['project_sha256']
    for target in TARGETS:assert b.sha(target) in [report['baseline_sha256'],report['project_sha256']]
    for target in TARGETS:shutil.copy2(source,target)
    shutil.copy2(REVIEW/'validation.json',PACKAGE/'cover-edge-validation.json')
    assert b.sha(TARGETS[0])==b.sha(TARGETS[1])==report['project_sha256']
    print('Published both normal Dara project files.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['stage','slice','verify','publish'])
    {'stage':stage,'slice':slice_native,'verify':verify,'publish':publish}[parser.parse_args().action]()
