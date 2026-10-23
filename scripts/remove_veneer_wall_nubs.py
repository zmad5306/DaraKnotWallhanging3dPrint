"""Trim only isolated obsolete stem bases above the saved inclined wall."""
import sys,json,shutil,copy,re,hashlib
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'.work/python-libs'),str(Path(__file__).parent)]
import correct_veneer_edge_connections as edge
from correct_veneer_edge_connections import *
import validate_veneer_edge_connections as validator
import organize_root_projects as org

WORK=ROOT/'.work/veneer-nub-cleanup-r8'
REPORT=ROOT/'release/veneer-nub-cleanup-r8'
SAMPLE=ROOT/'release/samples/Dara-A2L-Hammered-Finish-ERYONE-r4.3mf'
TARGETS={'Letter':WORK/'Letter-cleaned.3mf','ERYONE-r4':WORK/'ERYONE-r4-cleaned.3mf'}

def cleanup(body,region,contacts):
    g=cleanup.context.pop(0)
    old=np.array([c['old_xy_mm'] for c in g['connections']]);nubs=[];cutters=[]
    # Detect disconnected cross-sections just ABOVE the flat wall. Active
    # connections reach the ceiling of this slab and are never selected.
    for piece in (body^slab(4.4001,5.7)).decompose():
        bb=np.array(piece.bounding_box()).reshape(2,3)
        distance=float(np.min(np.linalg.norm(old-bb.mean(0)[:2],axis=1)))
        if bb[1,2]>=5.6999 or distance>=4:continue
        assert piece.volume()<2 and np.max(bb[1,:2]-bb[0,:2])<4
        lo=bb[0,:2]-.0001;size=bb[1,:2]-bb[0,:2]+.0002
        cutters.append(block(*size,1.3,[*lo,4.4]))
        nubs.append(dict(bounds_mm=bb.tolist(),measured_above_wall_mm3=piece.volume(),distance_to_old_connection_mm=distance))
    assert nubs
    tool=mf.Manifold.batch_boolean(cutters,mf.OpType.Add)
    result=body-tool;removed=body-result;added=result-body
    assert abs(added.volume())<1e-6
    above=abs((removed^slab(5.70001,1000)).volume())
    below=abs((removed^slab(-1000,4.39995)).volume())
    assert above+below<1e-6
    assert len([p for p in result.decompose() if p.volume()>1e-6])==1
    # Every selected wedge is now flush to the nominal wall plane; tolerances
    # only cover serialization, not a retained printable stem.
    assert abs((result^tool).volume())<1e-6
    remaining=[]
    for p in (result^slab(4.4001,5.7)).decompose():
        bb=np.array(p.bounding_box()).reshape(2,3)
        d=np.min(np.linalg.norm(old-bb.mean(0)[:2],axis=1))
        if bb[1,2]<5.6999 and d<4:remaining.append(p.volume())
    assert not remaining,remaining
    return result,dict(nubs=nubs,nub_count=len(nubs),removed_mm3=removed.volume(),added_mm3=added.volume(),
        removal_above_5_7mm_mm3=above,removal_below_wall_mm3=below,remaining_selected_nubs=0,
        connected_components=1,watertight=mesh(result).is_volume,connections=g['connections'])

def build():
    WORK.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
    protected={p.name:sha(p) for p in ROOT.glob('*.3mf')}
    for title,source in [('Letter',ROOT/'Letter.3mf'),('ERYONE-r4',SAMPLE)]:
        baseline=WORK/(title+'-before.3mf')
        if not baseline.exists():shutil.copyfile(source,baseline)
        else:assert sha(baseline)==sha(source)
        old=json.loads((ROOT/'release/veneer-edge-r7'/(title+'-geometry.json')).read_text())
        cleanup.context=copy.deepcopy(old['objects']);edge.repair=cleanup
        specs=[(r['name'],np.array(r['pose']),None,None) for r in old['objects']]
        report=edge.patch_project(baseline,TARGETS[title],specs)
        assert not cleanup.context
        (REPORT/(title+'-geometry.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(title,[g['nub_count'] for g in report['objects']],flush=True)
    (REPORT/'protected-projects-before.json').write_text(json.dumps(protected,indent=2)+'\n')

def configure():
    validator.WORK=WORK;validator.REPORT=REPORT;validator.TARGETS=TARGETS

def publish():
    configure()
    before=read(WORK/'Letter-before.3mf');files=read(TARGETS['Letter'])
    native=read(WORK/'native-Letter/sliced.3mf')
    # Retain original geometry, object metadata and every stored artifact for
    # core plates 1-3; replace native slice artifacts only for affected 4-6.
    cfg=ET.fromstring(files['Metadata/model_settings.config']);ncfg=ET.fromstring(native['Metadata/model_settings.config'])
    info=ET.fromstring(before['Metadata/slice_info.config']);ni=ET.fromstring(native['Metadata/slice_info.config'])
    seq=json.loads(before['Metadata/filament_sequence.json']);ns=json.loads(native['Metadata/filament_sequence.json'])
    for number in (4,5,6):
        cp=cfg.findall('plate')[number-1];np_=copy.deepcopy(ncfg.findall('plate')[number-1])
        oldid=org.props(cp.find('model_instance'))['object_id']
        newins=np_.find('model_instance');newins.find("metadata[@key='object_id']").set('value',oldid)
        pos=list(cfg).index(cp);cfg.remove(cp);cfg.insert(pos,np_)
        old=next(p for p in info.findall('plate') if org.props(p)['index']==str(number))
        new=next(p for p in ni.findall('plate') if org.props(p)['index']==str(number))
        pos=list(info).index(old);info.remove(old);info.insert(pos,copy.deepcopy(new))
        seq[f'plate_{number}']=ns[f'plate_{number}']
        pattern=re.compile(r'Metadata/(?:plate_|plate_no_light_|top_|pick_)'+str(number)+r'(?:_small)?\.(?:png|json|gcode(?:\.md5)?)$')
        files.update({n:v for n,v in native.items() if pattern.fullmatch(n)})
    for n,v in before.items():
        if re.fullmatch(r'Metadata/(?:plate_|plate_no_light_|top_|pick_)[123](?:_small)?\.(?:png|json|gcode(?:\.md5)?)',n):files[n]=v
    files['Metadata/model_settings.config']=xml(cfg)
    files['Metadata/slice_info.config']=xml(info)
    files['Metadata/filament_sequence.json']=json.dumps(seq,indent=2).encode()
    assert files['Metadata/project_settings.config']==before['Metadata/project_settings.config']
    protected_assets=[]
    changed=json.loads((REPORT/'Letter-geometry.json').read_text())['changed_assets']
    for n,v in before.items():
        if n.endswith('.model') and n not in changed:assert files[n]==v;protected_assets.append(n)
    for number in (1,2,3):
        for suffix in ('.gcode','.gcode.md5'):assert files[f'Metadata/plate_{number}{suffix}']==before[f'Metadata/plate_{number}{suffix}']
    write(WORK/'Letter-final.3mf',files)
    check=org.compare(WORK/'Letter-final.3mf',WORK/'native-Letter/sliced.3mf')
    for title in TARGETS:
        report=json.loads((REPORT/(title+'-native.json')).read_text())
        assert sha(WORK/('native-'+title)/'sliced.3mf')==report['native_sha256']
    shutil.copyfile(WORK/'Letter-final.3mf',ROOT/'Letter.3mf')
    shutil.copyfile(WORK/'native-ERYONE-r4/sliced.3mf',SAMPLE)
    protected=json.loads((REPORT/'protected-projects-before.json').read_text())
    for name,digest in protected.items():
        if name!='Letter.3mf':assert sha(ROOT/name)==digest
    catalog=json.loads((org.REPORT/'catalog.json').read_text());previous=catalog['Letter'];org.TITLES=['Letter'];dump=org.dump
    def merged(path,data):
        if path.name=='catalog.json':catalog['Letter']={**previous,**data['Letter']};return dump(path,catalog)
        return dump(path,data)
    org.dump=merged;org.export_cad()
    gcode=json.loads((org.REPORT/'gcode-sha256.json').read_text())
    gcode['Letter'].update({Path(n).stem:hashlib.sha256(v).hexdigest() for n,v in files.items() if n.endswith('.gcode')})
    dump(org.REPORT/'gcode-sha256.json',gcode)
    result=json.loads((WORK/'native-Letter/result.json').read_text());oldresult=json.loads((org.REPORT/'Letter-native.json').read_text())
    for i in range(3):result['sliced_plates'][i]=oldresult['sliced_plates'][i]
    dump(org.REPORT/'Letter-native.json',result)
    samples=json.loads((ROOT/'release/samples/catalog.json').read_text());samples['Dara-A2L-Hammered-Finish-ERYONE-r4'].update(sha256=sha(SAMPLE),validation='release/veneer-nub-cleanup-r8/ERYONE-r4-native.json')
    dump(ROOT/'release/samples/catalog.json',samples)
    dump(REPORT/'release.json',dict(main_sha256=sha(ROOT/'Letter.3mf'),sample_sha256=sha(SAMPLE),
        protected_core_mesh_assets=protected_assets,core_plate_artifacts_byte_preserved=True,
        native_geometry_and_settings_comparison=check,physical_validation_pending=True))
    print('Published cleaned meshes and synchronized release evidence.',flush=True)

if __name__=='__main__':
    action=sys.argv[1];configure()
    if action=='build':build()
    elif action=='slice':validator.slice_one(sys.argv[2])
    elif action=='validate':validator.validate(sys.argv[2])
    elif action=='publish':publish()
