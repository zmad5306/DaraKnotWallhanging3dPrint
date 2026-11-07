"""Support-only migration of the saved r9 production project; no geometry rebuild."""
from pathlib import Path
import copy, hashlib, importlib.util, json, re
import xml.etree.ElementTree as ET

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
spec=importlib.util.spec_from_file_location('bucket_builder',OUT/'build_bucket.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
WORK=ROOT/'.work/a2l-bucket-tree-supports-r10'
FINAL=OUT/'A2L-Poop-Bucket-A1-SUNLU-PLA.3mf'
SOURCE_SHA='e5cc8899d8bfc1ddcb7b1ff442e0e50ac2d14e7c4240c09f55e46b478a89b9f2'
CHANGES={'support_type':['normal(auto)','tree(auto)'],'support_style':['snug','default']}


def props(e):
    return {n.get('key'):n.get('value') for n in e.findall('metadata')
            if n.get('key') and not n.get('key').startswith('source_')}


def audit_overrides(files):
    c=ET.fromstring(files['Metadata/model_settings.config'])
    return {'objects':[{**props(o),'parts':[{**props(p),'id':p.get('id'),'subtype':p.get('subtype')}
              for p in o.findall('part')],'id':o.get('id')} for o in c.findall('object')],
            'plates':[props(p) for p in c.findall('plate')]}


def main():
    WORK.mkdir(parents=True,exist_ok=True)
    assert b.sha(FINAL)==SOURCE_SHA
    previous=json.loads((OUT/'validation.json').read_text());assert previous['sha256']==SOURCE_SHA
    (WORK/'before.3mf').write_bytes(FINAL.read_bytes())
    history=OUT/'history';history.mkdir(exist_ok=True)
    (history/'r9-validation.json').write_bytes((OUT/'validation.json').read_bytes())
    protected=list(ROOT.glob('*.3mf'))+[OUT/'Bucket.stl',OUT/'Bucket.scad',*sorted((OUT/'reference').glob('*'))]
    protected=[p for p in protected if p.is_file()]
    before={b.rel(p):b.sha(p) for p in protected}
    source=b.package(FINAL);old=json.loads(source['Metadata/project_settings.config'])
    cfg=copy.deepcopy(old)
    for k,(a,c) in CHANGES.items():assert cfg[k]==a;cfg[k]=c
    assert {k:[old.get(k),cfg.get(k)] for k in old.keys()|cfg.keys() if old.get(k)!=cfg.get(k)}==CHANGES
    files=dict(source);files['Metadata/project_settings.config']=json.dumps(cfg,indent=2).encode()
    editable=WORK/'tree-supports-editable.3mf';b.save(editable,files)
    print('Only support type and its compatible default style changed. Slicing A1 tree supports.',flush=True)
    result=b.native(editable,WORK/'slice',True)
    candidate=WORK/'slice/sliced.3mf';sliced=b.package(candidate)
    saved=json.loads(sliced['Metadata/project_settings.config']);assert saved==cfg
    assert audit_overrides(source)==audit_overrides(sliced)
    child_paths=[n for n in source if n.startswith('3D/Objects/') and n.endswith('.model')]
    assert child_paths
    for p in child_paths:assert source[p]==sliced[p],p
    a,c=b.saved_mesh(source),b.saved_mesh(sliced)
    assert b.np.array_equal(a.vertices,c.vertices) and b.np.array_equal(a.faces,c.faces)
    assert c.is_volume and len(c.split())==1
    root_a=ET.fromstring(source['3D/3dmodel.model']);root_c=ET.fromstring(sliced['3D/3dmodel.model'])
    def poses(r):
        return [e.attrib for e in r.findall(b.tag('build')+'/'+b.tag('item'))]+[
            e.attrib for e in r.findall('.//'+b.tag('component'))]
    assert poses(root_a)==poses(root_c)
    locked=copy.deepcopy(previous['locked_settings'])
    for k,values in CHANGES.items():locked[k]=values[1]
    for k,v in locked.items():assert saved[k]==v
    get_cfg=lambda s:dict(re.findall(r'^; (\w+) = (.*)$',s,re.M))
    old_gc=get_cfg(source['Metadata/plate_1.gcode'].decode())
    gc=sliced['Metadata/plate_1.gcode'].decode();new_gc=get_cfg(gc)
    gc_diff={k:[old_gc.get(k),new_gc.get(k)] for k in old_gc.keys()|new_gc.keys() if old_gc.get(k)!=new_gc.get(k)}
    assert gc_diff==CHANGES,gc_diff
    checksum=hashlib.md5(sliced['Metadata/plate_1.gcode']).hexdigest()
    assert sliced['Metadata/plate_1.gcode.md5'].decode().strip().lower()==checksum
    assert checksum!=previous['gcode_md5']
    audit=b.scan_gcode(gc.replace('; FEATURE: Support transition','; FEATURE: Support'))
    assert audit['features'].get('Support',0)>0 and audit['features'].get('Support interface',0)>0
    assert audit['features'].get('Sparse infill',0)>0 and 'Prime tower' not in audit['features']
    assert audit['conservative_bed_edge_clearance_mm']>0
    zs=audit['model_extrusion_z_by_filament_mm'];assert list(zs)==['1'] and len(zs['1'])==754
    info=ET.fromstring(sliced['Metadata/slice_info.config']);warnings=[e.attrib for e in info.findall('plate/warning')]
    assert all(w['msg']=='not_support_traditional_timelapse' for w in warnings),warnings
    assert info.find('plate/filament').get('tray_info_idx')==cfg['filament_ids'][0]
    estimate=result['sliced_plates'][0];times=estimate['times']
    assert times['support_tree_generate_time']>0 and times['support_normal_generate_time']==0,times
    reopen=b.native(candidate,WORK/'reopened')
    assert get_cfg((WORK/'reopened/plate_1.gcode').read_text())==new_gc
    assert reopen['sliced_plates'][0]['times']['support_tree_generate_time']>0
    after={b.rel(p):b.sha(p) for p in protected};assert before==after
    FINAL.write_bytes(candidate.read_bytes())
    revision={'source_project':b.rel(FINAL),'source_sha256':SOURCE_SHA,'sha256':b.sha(FINAL),
              'source_commit':'ddf4a121e8993008e7d491dd0e2d8d532a670b19',
              'changes':CHANGES,'gcode_config_changes':gc_diff,
              'all_other_global_settings_identical':True,'object_volume_plate_settings_identical':True,
              'mesh_xml_byte_identical':{p:hashlib.sha256(source[p]).hexdigest() for p in child_paths},
              'vertices_faces_and_poses_exactly_equal':True,'native_slice':result,'native_reopen':reopen,
              'gcode_md5':checksum,'toolpath_audit':audit,'warnings':warnings,
              'protected_before':before,'protected_after':after,
              'estimated_seconds':estimate['total_predication'],'estimated_pla_g':estimate['filaments'][0]['total_used_g'],
              'previous_estimated_seconds':previous['estimated_seconds'],'previous_estimated_pla_g':previous['estimated_pla_g'],
              'physical_tree_support_result':'Not yet observed; no printer job sent.'}
    (history/'tree-supports-r10.json').write_text(json.dumps(revision,indent=2)+'\n',encoding='utf8')
    report=copy.deepcopy(previous)
    report.update(revision='r10',sha256=b.sha(FINAL),locked_settings=locked,native_slice=result,native_reopen=reopen,
                  gcode_md5=checksum,toolpath_audit=audit,warnings=warnings,estimated_seconds=estimate['total_predication'],
                  estimated_pla_g=estimate['filaments'][0]['total_used_g'],support_revision=revision,
                  user_support_approval='2026-11-07: Switch the project to tree supports, commit and push.')
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    (OUT/'native-preview.png').write_bytes(sliced['Metadata/plate_1.png'])
    c.apply_translation(-c.bounds[0]);floor=b.section(b.solid(c))
    raw=b.np.load(OUT/'reference/accepted-r8-mesh.npz')
    fit=b.trimesh.Trimesh(raw['vertices'],raw['faces'],process=False)
    template=b.translate(b.section(b.solid(fit)),xoff=report['registration_xy_mm'][0],yoff=report['registration_xy_mm'][1])
    b.render_preview(floor,template,report)
    print(json.dumps({k:revision[k] for k in ['sha256','changes','estimated_seconds','estimated_pla_g']},indent=2))
    print('Native tree generation ms:',times['support_tree_generate_time'],'Bed edge clearance mm:',audit['conservative_bed_edge_clearance_mm'])


if __name__=='__main__':main()
