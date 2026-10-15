"""Append a full-color, unscaled F7/F4 epoxy assembly sample to complete Dara.

Crop the current project meshes and modifiers, retaining the native keyed lap.
Stage, slice in Bambu Studio, verify, then publish both normal project copies.
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

from integrate_hammered_dara import (
    ROOT, PACKAGE, TARGETS, selected_entries, plate_offset, relationship_xml,
    digest, props, setmeta, read_zip, write_zip, sha, xml, tag, P, R, uid,
    np, transform, cKDTree, model_entries, scan_gcode,
)
from build_jointed_bambu_project import read_array, model, mesh_object, meta, IDENTITY
from prepare_hammered_bands import boolean, rotation, trimesh, mesh_slice

WORK = ROOT / '.work/knot-glue-sample'
REVIEW = ROOT / 'working/review/knot-glue-sample'
REPORT = PACKAGE / 'knot-glue-sample-validation.json'
N = 32
NAMES = ['Knot-Joint-A-F7', 'Knot-Joint-B-F4']
CROP_LOW, CROP_HIGH = [-32., -34., -1.], [42., 34., 20.]


def stage():
    WORK.mkdir(parents=True, exist_ok=True); REVIEW.mkdir(parents=True, exist_ok=True)
    baseline = WORK / 'baseline.3mf'
    if not baseline.exists():
        assert sha(TARGETS[0]) == sha(TARGETS[1])
        shutil.copy2(TARGETS[0], baseline)
    assert sha(baseline) == sha(TARGETS[0]), 'Production changed since staging.'
    evidence = json.loads((PACKAGE / 'hammered-integration-validation.json').read_text())
    assert evidence['project_sha256'] == sha(baseline)
    files = read_zip(baseline)
    root = ET.fromstring(files['3D/3dmodel.model'])
    cfg = ET.fromstring(files['Metadata/model_settings.config'])
    rels = ET.fromstring(files['3D/_rels/3dmodel.model.rels'])
    assert len(cfg.findall('plate')) == 31
    source = selected_entries(files, {'F7', 'F4'})
    cad = (ROOT / 'working/Dara-Photo-Frame-A1-Jointed.scad').read_text()
    placements = read_array(cad, 'frame_placements'); joint = read_array(cad, 'frame_joints')[0]
    assert joint[:2] == [6, 3]
    crop = trimesh.creation.box(np.array(CROP_HIGH)-CROP_LOW)
    crop.apply_translation((np.array(CROP_HIGH)+CROP_LOW)/2)
    resources, build = root.find(tag('resources')), root.find(tag('build'))
    pc = ET.SubElement(cfg, 'plate')
    for k,v in [('plater_id', N), ('plater_name', '32 - Full-color knot joint - epoxy practice'),
                ('locked','false'), ('filament_map_mode','Auto For Flush'),
                ('filament_maps','1 1 1 1'), ('filament_volume_maps','0 0 0 0')]: meta(pc,k,v)
    records = []
    for i,(oldname,name) in enumerate(zip(['F7','F4'], NAMES)):
        original_config = next(o for o in cfg.findall('object') if props(o)['name']==oldname)
        original_build = next(b for b in build if b.get('objectid')==original_config.get('id'))
        p = placements[int(oldname[1:])-1]
        unplace = np.eye(4); unplace[:3,3] = [*p[1],-p[3]]
        origin = np.eye(4); origin[:2,3] = -np.array(joint[2])
        to_joint = rotation(-joint[3]) @ origin @ rotation(-p[0]) @ unplace @ np.linalg.inv(transform(original_build.get('transform')))
        parts = []; source_checks = []
        for part in source[oldname]:
            assert not part['paint'].any(), 'Painted supports require clipping their face assignments too.'
            m = part['mesh'].copy(); m.apply_transform(to_joint)
            clipped = boolean([m,crop], 'intersection')
            if abs(clipped.volume) < 1e-6: continue
            # Round-trip through a crop must not add material outside the original.
            excess = boolean([clipped,m], 'difference')
            # Repeating a boolean on coincident modifier relief can leave a
            # numerical sliver (<0.01 mm3 here); bound it relative to the crop.
            assert abs(excess.volume)<max(1e-5,abs(clipped.volume)*1e-5),(oldname,props(part['config'])['name'],excess.volume,clipped.volume)
            cp = copy.deepcopy(part['config'])
            for md in list(cp.findall('metadata')):
                key=md.get('key','')
                if key=='matrix' or key.startswith('source_'): cp.remove(md)
            cp.attrib.pop('uuid',None)
            parts.append((clipped,cp))
            source_checks.append(dict(name=props(cp)['name'],subtype=cp.get('subtype'),
                                     volume_mm3=float(clipped.volume),added_outside_source_mm3=float(excess.volume)))
        assert parts[0][1].get('subtype')=='normal_part'
        body=parts[0][0]
        assert body.is_volume and len(body.split(only_watertight=False))==1
        assert {props(c).get('extruder') for m,c in parts} >= {'1','2','4'}
        assert body.extents[1]>67 and body.extents[2]==13.5
        np.savez_compressed(WORK/f'{name}.npz',vertices=body.vertices,faces=body.faces)
        for mesh,cp in parts:
            if props(cp).get('extruder') in ['2','4']:
                mesh.export(WORK/f'{name}-color-{props(cp)["extruder"]}.ply')
        # Preserve each parent's XY print rotation and original Z datum.
        yaw = p[0]+joint[3]; turn=rotation(yaw)
        placed=body.copy(); placed.apply_transform(turn)
        low=np.array([30.,55.]) if i==0 else np.array([135.,55.])
        turn[:2,3]=low-placed.bounds[0,:2]
        bounds=trimesh.transform_points(body.vertices,turn)
        bounds=np.array([bounds.min(axis=0),bounds.max(axis=0)])
        assert min(*bounds[0,:2],*(256-bounds[1,:2]))>8
        oid=32000+i*100; path=f'3D/Objects/{name}.model'
        child=model(); cr=ET.SubElement(child,tag('resources'))
        obj=ET.SubElement(resources,tag('object'),id=str(oid),type='model',attrib={'{'+P+'}UUID':uid()})
        comps=ET.SubElement(obj,tag('components'))
        co=ET.SubElement(cfg,'object',id=str(oid))
        # Same production process; source object metadata includes a non-setting
        # face-count node with no key, which is deliberately not copied.
        for k,v in props(original_config).items():
            if k: meta(co,k,v)
        setmeta(co,'name',name); setmeta(co,'extruder',1)
        for j,(m,cp) in enumerate(parts,1):
            pid=oid+j; cp.set('id',str(pid)); co.append(cp)
            if j==1: setmeta(cp,'name',name)
            mesh_object(cr,pid,m)
            ET.SubElement(comps,tag('component'),objectid=str(pid),transform=IDENTITY,
                          attrib={'{'+P+'}path':'/'+path,'{'+P+'}UUID':uid()})
        files[path]=xml(child)
        ET.SubElement(rels,'{'+R+'}Relationship',Target='/'+path,Id=f'knot-sample-{oid}',
                      Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
        project_t=turn.copy(); project_t[:2,3]+=plate_offset(N,6)
        ET.SubElement(build,tag('item'),objectid=str(oid),printable='1',
                      transform=' '.join(f'{v:.12g}' for v in project_t[:3,:].T.ravel()),attrib={'{'+P+'}UUID':uid()})
        inst=ET.SubElement(pc,'model_instance')
        for k,v in [('object_id',oid),('instance_id',0),('identify_id',oid)]:meta(inst,k,v)
        records.append(dict(name=name,source=oldname,object_id=oid,identify_id=str(oid),
                            bounds_assembled_mm=body.bounds.tolist(),bounds_on_plate_mm=bounds.tolist(),
                            build_transform=turn.tolist(),source_to_joint=to_joint.tolist(),
                            components=source_checks,watertight=True,volume_mm3=float(body.volume)))
    a,b=[load_body(name) for name in NAMES]
    overlap=boolean([a,b],'intersection')
    assert abs(overlap.volume)<1e-5,overlap.volume
    cfg[:]=cfg.findall('object')+cfg.findall('plate')+cfg.findall('assemble')
    settings=json.loads(files['Metadata/project_settings.config'])
    for k,v in [('wipe_tower_x','185'),('wipe_tower_y','190')]:
        assert len(settings[k])==31;settings[k].append(v)
    files.update({'3D/3dmodel.model':xml(root),'3D/_rels/3dmodel.model.rels':relationship_xml(rels),
                  'Metadata/model_settings.config':xml(cfg),'Metadata/project_settings.config':json.dumps(settings,indent=2).encode()})
    write_zip(WORK/'staged.3mf',files)
    bounds=np.array([np.minimum(a.bounds[0],b.bounds[0]),np.maximum(a.bounds[1],b.bounds[1])])
    report=dict(baseline_sha256=sha(baseline),plate=N,joint=1,source_parts=['F7','F4'],
                crop_low_mm=CROP_LOW,crop_high_mm=CROP_HIGH,assembled_bounds_mm=bounds.tolist(),
                assembled_size_mm=(bounds[1]-bounds[0]).tolist(),mating_intersection_mm3=float(overlap.volume),
                scale=1.0,parts=records)
    (WORK/'staged.json').write_text(json.dumps(report,indent=2)+'\n')
    render(report)
    print(json.dumps(report,indent=2),flush=True)


def load_body(name):
    a=np.load(WORK/f'{name}.npz');return trimesh.Trimesh(a['vertices'],a['faces'],process=False)


def render(report):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from shapely.plotting import plot_polygon
    from shapely.affinity import translate
    fig,axes=plt.subplots(1,2,figsize=(12,6));fig.patch.set_facecolor('#e4e7ec')
    for ax,(title,exploded) in zip(axes,[('Assembled — decorative face',False),('Separated — F7 tongue / F4 socket',True)]):
        ax.set_facecolor('#e4e7ec')
        def draw(poly,color,shift):
            for p in getattr(poly,'geoms',[poly]):
                if not p.is_empty:plot_polygon(translate(p,xoff=shift),ax=ax,add_points=False,facecolor=color,edgecolor='#777777',alpha=1,linewidth=.25)
        for i,name in enumerate(NAMES):
            shift=(-12 if i==0 else 12) if exploded else 0
            body=load_body(name)
            draw(mesh_slice(body,4), '#bdbbb3',shift)
            draw(mesh_slice(body,5.5), '#e1ded4',shift)
            draw(mesh_slice(body,8.5), '#bd9868',shift)
            draw(mesh_slice(body,9.85), '#a47c49',shift)
            draw(mesh_slice(body,13.49), '#f4f2eb',shift)
            mask=trimesh.load_mesh(WORK/f'{name}-color-4.ply')
            draw(mesh_slice(mask,13.2),'#176bb5',shift)
            ax.text(-17+shift if i==0 else 32+shift,-39,'A · F7' if i==0 else 'B · F4',ha='center',fontsize=12)
        ax.set(xlim=(-48,59),ylim=(-44,39),title=title,aspect='equal');ax.set_axis_off()
    fig.suptitle('Plate 32 — knot joint for epoxy practice',fontsize=19)
    size=report['assembled_size_mm']
    fig.text(.5,.035,f'{size[0]:.0f} × {size[1]:.1f} × {size[2]:.1f} mm assembled · Original keys, lap and color boundaries\nPlan view from actual mesh sections; colors show assignments, not predicted finish.',ha='center',fontsize=11)
    fig.tight_layout(rect=(0,.055,1,.95));fig.savefig(REVIEW/'joint-sample.png',dpi=150);plt.close(fig)


def slice_plate():
    out=WORK/'slice';out.mkdir(exist_ok=True)
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    with (out/'cli.log').open('w') as log:
        result=subprocess.run([str(exe),'--slice',str(N),'--export-3mf','sliced.3mf',
                               '--outputdir',str(out),str(WORK/'staged.3mf')],cwd=exe.parent,
                              stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode==0,result.returncode
    print((out/'result.json').read_text(),flush=True)


def verify():
    staged=json.loads((WORK/'staged.json').read_text());assert sha(WORK/'baseline.3mf')==staged['baseline_sha256']
    original=read_zip(WORK/'baseline.3mf');files=read_zip(WORK/'staged.3mf');sliced=read_zip(WORK/'slice/sliced.3mf')
    result=json.loads((WORK/'slice/result.json').read_text());assert result['return_code']==0 and result['plate_index']==N
    ss=json.loads(sliced['Metadata/project_settings.config']);expected_settings=json.loads(files['Metadata/project_settings.config'])
    assert all(ss[k]==v for k,v in expected_settings.items())
    extras={k:v for k,v in ss.items() if k not in expected_settings}
    assert extras=={'different_settings_to_system':['']*6,'inherits_group':['']*6,'filament_map_2':['1']},extras
    expected=selected_entries(files,set(NAMES));actual=model_entries(sliced)
    assert set(actual)==set(NAMES)
    assert all(not p['paint'].any() for parts in selected_entries(original,{'F7','F4'}).values() for p in parts)
    mesh_checks=[]
    for name in NAMES:
        assert len(actual[name])==len(expected[name])
        for a,e in zip(actual[name],expected[name]):
            error=max(cKDTree(a['mesh'].vertices).query(e['mesh'].vertices)[0].max(),cKDTree(e['mesh'].vertices).query(a['mesh'].vertices)[0].max())
            assert error<.00015,(name,error)
            assert a['config'].get('subtype')==e['config'].get('subtype')
            for key in ['extruder','sparse_infill_density','sparse_infill_pattern']:
                assert props(a['config']).get(key)==props(e['config']).get(key)
            mesh_checks.append(dict(name=name,part=props(e['config'])['name'],max_vertex_error_mm=float(error)))
    sc=ET.fromstring(sliced['Metadata/model_settings.config']);cfg=ET.fromstring(files['Metadata/model_settings.config'])
    stats=ET.fromstring(sliced['Metadata/slice_info.config']);assert len(stats.findall('plate'))==1
    stat=stats.find('plate');p=props(stat)
    assert p['index']==str(N) and p['outside']=='false' and p['pause_count']=='0'
    assert {f.get('id') for f in stat.findall('filament')}=={'1','2','4'}
    assert {o.get('identify_id') for o in stat.findall('object')}=={str(r['object_id']) for r in staged['parts']}
    assert all(w.get('msg')=='not_support_traditional_timelapse' for w in stat.findall('warning'))
    setmeta(stat,'printer_model_id','N2S')
    first=float(p.get('first_layer_time','0'))
    if not math.isfinite(first) or not 0<=first<=float(p['prediction']):stat.remove(stat.find("metadata[@key='first_layer_time']"))
    data=sliced[f'Metadata/plate_{N}.gcode'];text=data.decode()
    assert hashlib.md5(data).hexdigest().lower()==sliced[f'Metadata/plate_{N}.gcode.md5'].decode().strip().lower()
    audit=scan_gcode(text);assert audit['conservative_bed_edge_clearance_mm']>3
    assert set(audit['model_extrusion_z_by_filament_mm'])=={'1','2','4'}
    color_ranges={k:[min(v),max(v)] for k,v in audit.pop('model_extrusion_z_by_filament_mm').items()}
    assert color_ranges['2'][0]>=8.399 and color_ranges['2'][1]<=10.01
    assert color_ranges['4'][0]>=12.899 and color_ranges['4'][1]<=13.601
    for feature in ['Support','Support interface','Sparse infill','Prime tower']:
        assert audit['features'].get(feature,0)>0,feature
    assert not re.search(r'^\s*(?:M400\s+U1|M0(?:\s|$)|M1(?:\s|$)|M25(?:\s|$))',text,re.M)
    plate=cfg.findall('plate')[-1];sp=next(p for p in sc.findall('plate') if props(p)['plater_id']==str(N))
    assert props(plate)['plater_id']==props(sp)['plater_id']==str(N)
    for md in sp.findall('metadata'):
        k,v=md.get('key'),md.get('value')
        if k.endswith('_file') and v:setmeta(plate,k,v);files[v]=sliced[v]
    for path,data in sliced.items():
        if re.match(rf'Metadata/plate_{N}(?:\.|_)',path):files[path]=data
    info=ET.fromstring(files['Metadata/slice_info.config']);info.append(stat)
    seq=json.loads(files['Metadata/filament_sequence.json']);seq[f'plate_{N}']=json.loads(sliced['Metadata/filament_sequence.json'])[f'plate_{N}']
    relpath='Metadata/_rels/model_settings.config.rels';rels=ET.fromstring(files[relpath])
    ET.SubElement(rels,'{'+R+'}Relationship',Target=f'/Metadata/plate_{N}.gcode',Id=f'rel-{N}',Type='http://schemas.bambulab.com/package/2021/gcode')
    files.update({'Metadata/model_settings.config':xml(cfg),'Metadata/slice_info.config':xml(info),
                  'Metadata/filament_sequence.json':json.dumps(seq).encode(),relpath:relationship_xml(rels)})
    # Existing models, overrides, transforms and native slices are untouched.
    oldcfg=ET.fromstring(original['Metadata/model_settings.config']);newroot=ET.fromstring(files['3D/3dmodel.model']);oldroot=ET.fromstring(original['3D/3dmodel.model'])
    for obj in oldcfg.findall('object'):assert xml(obj)==xml(cfg.find(f"object[@id='{obj.get('id')}']"))
    for old,new in zip(oldcfg.findall('plate'),cfg.findall('plate')):assert xml(old)==xml(new)
    for old,new in zip(oldroot.find(tag('resources')),newroot.find(tag('resources'))):assert xml(old)==xml(new)
    for old,new in zip(oldroot.find(tag('build')),newroot.find(tag('build'))):assert xml(old)==xml(new)
    preserved=[]
    for path,data in original.items():
        if path.startswith('3D/Objects/') or re.match(r'Metadata/(?:plate_|plate_no_light_|top_|pick_)\d+[_.]',path):assert data==files[path],path
    for n in range(1,N):preserved.append(dict(plate=n,gcode_sha256=digest(files[f'Metadata/plate_{n}.gcode'])))
    for k,v in json.loads(original['Metadata/project_settings.config']).items():
        if k in ['wipe_tower_x','wipe_tower_y']:assert expected_settings[k][:-1]==v
        else:assert expected_settings[k]==v,k
    assert len(cfg.findall('plate'))==len(info.findall('plate'))==N
    assert len(cfg.findall('object'))==47 and len(newroot.find(tag('build')))==78
    write_zip(WORK/'complete.3mf',files)
    totals=[dict(plate=int(props(p)['index']),weight_g=float(props(p)['weight']),seconds=int(props(p)['prediction'])) for p in info.findall('plate')]
    audit.update(plate=N,gcode_sha256=digest(files[f'Metadata/plate_{N}.gcode']),weight_g=float(p['weight']),
                 seconds=int(p['prediction']),model_z_ranges_by_filament_mm=color_ranges)
    report=dict(date='2026-10-15',project_sha256=sha(WORK/'complete.3mf'),baseline_sha256=staged['baseline_sha256'],
                plates=N,production_pieces=75,optional_test_pieces=3,sample=staged,changed_plates=[audit],
                unchanged_native_plates=preserved,mesh_checks=mesh_checks,all_plate_estimates=totals,
                total_weight_g=sum(t['weight_g'] for t in totals),total_seconds=sum(t['seconds'] for t in totals),
                scope='Unscaled crop of native F7/F4 joint 1 with its original white/wood/blue modifiers and print orientation. Digital checks passed; epoxy cleanup, clamp method and bond strength require physical trial.')
    (WORK/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(audit,indent=2),flush=True)


def publish():
    report=json.loads((WORK/'validation.json').read_text());candidate=WORK/'complete.3mf'
    assert sha(candidate)==report['project_sha256']
    for target in TARGETS:assert sha(target) in [report['baseline_sha256'],report['project_sha256']]
    for target in TARGETS:shutil.copy2(candidate,target)
    shutil.copy2(WORK/'validation.json',REPORT)
    print('Published plate 32 in both normal Dara files.',flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['stage','slice','verify','publish'])
    action=ap.parse_args().action
    {'stage':stage,'slice':slice_plate,'verify':verify,'publish':publish}[action]()
