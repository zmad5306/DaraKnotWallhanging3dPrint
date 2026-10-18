"""Verify packed tests against their originals and the native three-plate slice."""
import argparse
import collections
import copy
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile
import numpy as np
from development_3mf import OUT,WORK,read_object,sha,save_json,tag,P,props
from validate_development_candidates import validate,coupon_connectivity
from validate_print_project import scan_gcode,TOKEN
from check_fin_toolpaths import check_fin_bonds
from combine_development_tests import NAME


def read(path):
    with zipfile.ZipFile(path) as z:return {n:z.read(n) for n in z.namelist()}


def frame_grain(text,rows,label_ids):
    by_id={label_ids[r['name']]:r for r in rows if r['plate']==3}
    current=None;feature='Custom';x=y=z=e=0.;relative=False;xyz=False;tool=None
    groups=collections.defaultdict(lambda:collections.defaultdict(collections.Counter))
    for raw in text.splitlines():
        if raw.startswith('; start printing object, unique label id: '):current=int(raw.rsplit(': ',1)[1])
        elif raw.startswith('; stop printing object, unique label id: '):current=None
        elif raw.startswith('; FEATURE: '):feature=raw.split(': ',1)[1]
        code=raw.split(';',1)[0].strip()
        if not code:continue
        cmd=code.split()[0];v={k:float(n) for k,n in TOKEN.findall(code)}
        if cmd in ['T0','T1','T2','T3']:tool=int(cmd[1:])+1
        elif cmd=='M83':relative=True
        elif cmd=='M82':relative=False
        elif cmd in ['G90','G91']:xyz=cmd=='G91'
        elif cmd=='G92':x,y,z,e=[v.get(k,o) for k,o in zip('XYZE',(x,y,z,e))]
        elif cmd in ['G0','G1','G2','G3']:
            nx,ny,nz=[o+v.get(k,0) if xyz else v.get(k,o) for k,o in zip('XYZ',(x,y,z))]
            de=v.get('E',0) if relative else v.get('E',e)-e;length=math.hypot(nx-x,ny-y)
            if cmd=='G1' and feature=='Top surface' and de>0 and length>.5 and current in by_id and tool in [1,2,4]:
                row=by_id[current];r=np.array(row['assembly_to_printer'])
                yaw=math.degrees(math.atan2(r[1,0],r[0,0]))
                angle=round(((math.degrees(math.atan2(ny-y,nx-x))-yaw)%180)*2)/2
                assembly_z=nz-r[2,3]
                key=(row['name'][0],tool,round(assembly_z,2));side='tongue' if 'tongue' in row['name'] else 'socket'
                groups[key][side][angle]+=length
            x,y,z=nx,ny,nz;e=e+v.get('E',0) if relative else v.get('E',e)
    evidence=[]
    for (variant,tool,z),sides in sorted(groups.items()):
        if any(sum(sides[k].values())<10 for k in ['tongue','socket']):continue
        angles=[sides[k].most_common(1)[0][0] for k in ['tongue','socket']]
        assert abs((angles[0]-angles[1]+90)%180-90)<1,(variant,tool,z,angles)
        if tool==1 and z>13.3:assert all(abs(a-135)<1 for a in angles),(variant,angles)
        evidence.append(dict(variant=variant,filament_slot=tool,z_mm=z,assembly_angles_deg=angles))
    for variant in ['Z']:
        assert any(r['variant']==variant and r['filament_slot']==1 and r['z_mm']>13.3 for r in evidence),('No white finish evidence',variant)
        assert any(r['variant']==variant and r['filament_slot']==2 for r in evidence),('No wood finish evidence',variant)
        assert any(r['variant']==variant and r['filament_slot']==4 for r in evidence),('No blue finish evidence',variant)
    return evidence


def main(native=None,preserved_plates=(1,3)):
    guide=json.loads((OUT/(NAME+'.json')).read_text());staged=OUT/(NAME+'.3mf');files=read(staged)
    cfg=ET.fromstring(files['Metadata/model_settings.config']);root=ET.fromstring(files['3D/3dmodel.model'])
    rows=guide['records'];assert len(rows)==11 and len(cfg.findall('plate'))==3
    sources={s['file']:read(OUT/s['file']) for s in guide['sources']}
    for source in guide['sources']:assert sha(OUT/source['file'])==source['sha256']
    checks=[]
    for row in rows:
        original=sources[row['source_project']];oldid=str(row['source_object_id']);newid=str(row['object_id'])
        oldcfg=ET.fromstring(original['Metadata/model_settings.config']);oldroot=ET.fromstring(original['3D/3dmodel.model'])
        oldobj=oldcfg.find(f"object[@id='{oldid}']");newobj=cfg.find(f"object[@id='{newid}']")
        assert {k:v for k,v in props(oldobj).items() if k!='name'}=={k:v for k,v in props(newobj).items() if k!='name'}
        oldparts,oldsettings=read_object(original,oldid);newparts,newsettings=read_object(files,newid)
        for a,b in zip(oldparts,newparts):
            assert a['subtype']==b['subtype'] and a['settings']==b['settings']
            assert np.array_equal(a['mesh'].vertices,b['mesh'].vertices) and np.array_equal(a['mesh'].faces,b['mesh'].faces)
        old_top=oldroot.find(tag('resources')).find(f"{tag('object')}[@id='{oldid}']")
        new_top=root.find(tag('resources')).find(f"{tag('object')}[@id='{newid}']")
        for a,b in zip(old_top.find(tag('components')),new_top.find(tag('components'))):
            assert a.get('transform')==b.get('transform')
            path=b.get('{'+P+'}path').lstrip('/')
            child=ET.fromstring(files[path]);m=child.find(tag('resources')).find(f"{tag('object')}[@id='{b.get('objectid')}']").find(tag('mesh'))
            assert hashlib.sha256(ET.tostring(m)).hexdigest()==row['mesh_blocks_byte_identical'][b.get('objectid')]
        old=json.loads((OUT/row['source_project']).with_suffix('.json').read_text())
        oldrow=next(r for r in old['records'] if str(r['object_id'])==oldid)
        a,b=np.array(oldrow['assembly_to_printer']),np.array(row['assembly_to_printer'])
        assert np.allclose(a[:3,:3],b[:3,:3],atol=1e-12) and a[2,3]==b[2,3]
        checks.append(dict(name=row['name'],geometry_color_modifiers_support_paint_and_process_preserved=True,rotation_and_z_preserved=True))
    for i,a in enumerate(rows):
        for b in rows[:i]:
            if a['plate']!=b['plate']:continue
            aa,bb=np.array(a['body_bounds_mm']),np.array(b['body_bounds_mm'])
            overlap=np.minimum(aa[1,:2],bb[1,:2])-np.maximum(aa[0,:2],bb[0,:2])
            assert not np.all(overlap>0),(a['name'],b['name'],'Bounding boxes overlap')
    native=Path(native) if native is not None else WORK/'native-all-tests'
    validate(NAME+'.3mf',native)
    report_path=OUT/(NAME+'-native-validation.json');report=json.loads(report_path.read_text())
    report['coupon_connected_components']=dict(editable_source=coupon_connectivity(staged),native_export=coupon_connectivity(native/'sliced.3mf'))
    report['source_preservation']=checks
    copper=(native/'plate_2.gcode').read_text();bonds=[]
    for row in rows:
        if row['plate']!=2 or 'veneer' not in row['name']:continue
        seating=json.loads((OUT/(Path(row['source_project']).stem+'-seating.json')).read_text())
        carrier=copy.deepcopy(seating['panels'][row['source_plate']-2]['carrier'])
        delta=np.array([*row['xy_translation_from_source_mm'],0])
        carrier['bond_probes_print_xyz_mm']=(np.array(carrier['bond_probes_print_xyz_mm'])+delta).tolist()
        bonds.append(dict(name=row['name'],**check_fin_bonds(copper,carrier)))
    report['combined_bond_checks']=bonds
    m_seam=json.loads((OUT/'M-zero-gap-seam-validation.json').read_text())
    assert m_seam['nominal_cosmetic_gap_mm']==0 and m_seam['maximum_front_edge_mismatch_mm']<1e-6
    assert m_seam['veneer_interference_mm3']<1e-5 and m_seam['core_glue_gap_mm']==.2
    report['m_zero_gap_seam']=m_seam
    native_files=read(native/'sliced.3mf');ncfg=ET.fromstring(native_files['Metadata/model_settings.config'])
    ids={}
    for plate in ncfg.findall('plate'):
        for inst in plate.findall('model_instance'):
            p=props(inst);obj=ncfg.find(f"object[@id='{p['object_id']}']")
            ids[props(obj)['name']]=int(p['identify_id'])
    text=(native/'plate_3.gcode').read_text()
    report['ribbon_surface_directions']=frame_grain(text,rows,ids)
    only_tower='\n'.join(l if not l.startswith('; FEATURE: ') or l=='; FEATURE: Prime tower' else '; FEATURE: Custom' for l in text.splitlines())
    tower=np.array(scan_gcode(only_tower)['bead_xy_bounds_mm'])
    rect=guide['ribbon_tower_reserved_rectangle_mm']
    assert np.all(tower[0]>np.array(rect[:2])) and np.all(tower[1]<np.array(rect[2:])),('Tower outside reserved area',tower)
    report['prime_tower_bead_bounds_mm']=tower.tolist()
    preservation=json.loads((OUT/'Zero-gap-plate-preservation.json').read_text())
    assert preservation['project_sha256']==sha(native/'sliced.3mf')
    assert {r['plate'] for r in preservation['plates']}==set(preserved_plates)
    for row in preservation['plates']:
        assert row['gcode_byte_identical']
        assert sha(native/f"plate_{row['plate']}.gcode")==row['preserved_assets_sha256'][f"Metadata/plate_{row['plate']}.gcode"]
    report['preserved_plates']=preservation
    for p in report['plates'][:2]:assert not p['features'].get('Prime tower',0),('Unexpected tower on single-material plate',p['plate'])
    save_json(report_path,report)
    guide['native_slice_validated']=True;guide['native_project']=NAME+'-Sliced.3mf';guide['native_validation']=report_path.name
    save_json(OUT/(NAME+'.json'),guide)
    print('Verified all 11 source parts, three packed plates, bonded fins, zero-gap ribbon grain, and reserved purge tower.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--native',type=Path)
    parser.add_argument('--preserved-plates',type=int,nargs='+',default=[1,3])
    args=parser.parse_args();main(args.native,args.preserved_plates)
