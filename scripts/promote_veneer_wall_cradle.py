"""Promote the approved r5 meshes into A2L plates 15-17, preserving all others.

Historical migration: inputs are the reviewed r5 projects and the immutable
pre-promotion snapshot. The published editable 3MF is the resulting mesh source.
No printer commands are sent. Never rebuild the unrelated knot or M cores.
"""
import argparse,copy,hashlib,json,re,shutil,subprocess,sys,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.work/python-libs'))
import numpy as np
from scipy.spatial import cKDTree
from development_3mf import sha,save_json,props,tag,transform,xml
from validate_print_project import scan_gcode

OUT=ROOT/'working/bambu/Dara-Photo-Frame-A2L'
REVIEW=ROOT/'output/Dara-A2L-Veneer-Wall-Cradle-r5'
WORK=ROOT/'.work/veneer-wall-production'
BASE=WORK/'baseline'
NATIVE=WORK/'native'
EDIT=WORK/'wall-cradle-editable.3mf'
P='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
EXPECTED_SOURCE='4aade57d5a92c152c697c25e2ae6f9813e6dac5f28bfe53ef03e7155bfa805e8'
REVISION='wall-cradle-r5'
CHANGED={15,16,17}
EXE=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')


def read(path):
    with zipfile.ZipFile(path) as z:return {n:z.read(n) for n in z.namelist()}


def write(path,files):
    path.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for n,v in files.items():z.writestr(n,v)


def selected(files,number):
    cfg=ET.fromstring(files['Metadata/model_settings.config'])
    root=ET.fromstring(files['3D/3dmodel.model'])
    plate=cfg.findall('plate')[number-1]
    assert len(plate.findall('model_instance'))==1
    oid=props(plate.find('model_instance'))['object_id']
    obj=cfg.find(f"object[@id='{oid}']")
    component=root.find(tag('resources')).find(f"{tag('object')}[@id='{oid}']").find(tag('components'))
    assert len(component)==1
    component=component[0];path=component.get(P+'path').lstrip('/')
    child=ET.fromstring(files[path])
    mesh=child.find(tag('resources')).find(f"{tag('object')}[@id='{component.get('objectid')}']").find(tag('mesh'))
    t=transform(root.find(tag('build')).find(f"{tag('item')}[@objectid='{oid}']").get('transform'))
    cols=int(np.ceil(np.sqrt(len(cfg.findall('plate')))));pi=number-1
    t[:2,3]-=[pi%cols*396,-(pi//cols)*384]
    return cfg,plate,obj,path,child,mesh,t@transform(component.get('transform'))


def vertices(mesh):return np.array([[float(v.get(k)) for k in ('x','y','z')] for v in mesh.find(tag('vertices'))])


def setmeta(node,key,value):
    item=node.find(f"metadata[@key='{key}']")
    if item is None:item=ET.SubElement(node,'metadata',key=key)
    item.set('value',str(value))


def snapshot():
    assert sha(ROOT/'Dara.3mf')==EXPECTED_SOURCE
    paths=[ROOT/'Dara.3mf',*OUT.glob('*'),ROOT/'output/development/m-veneer-cosmetic-fit/All-veneer-production-audit.json']
    for source in paths:
        if not source.is_file():continue
        target=BASE/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert sha(target)==sha(source)
        else:shutil.copyfile(source,target)
    external=[*(ROOT/'working/bambu/Dara-A1-Companion').glob('*'),
        ROOT/'working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf',
        ROOT/'output/development/m-veneer-cosmetic-fit/All-Development-Tests-A1-Sliced.3mf']
    save_json(WORK/'protected.json',{p.relative_to(ROOT).as_posix():sha(p) for p in external if p.is_file()})
    print('Immutable production snapshot saved.',flush=True)


def patch(source,target):
    original=read(source);files=dict(original);changed=[]
    review=json.loads((REVIEW/'validation.json').read_text())
    assert review['source_sha256']==EXPECTED_SOURCE
    for number in sorted(CHANGED):
        i=number-14;item=review['files'][i-1]
        candidate=REVIEW/Path(item['editable_file']).name
        assert sha(candidate)==item['editable_sha256']
        one=read(candidate)
        cfg,plate,obj,path,child,oldmesh,t=selected(files,number)
        _,_,newobj,_,_,newmesh,nt=selected(one,1)
        assert {k:v for k,v in props(obj).items() if k not in [None,'name']}=={k:v for k,v in props(newobj).items() if k not in [None,'name']}
        replacement=copy.deepcopy(newmesh)
        points=vertices(replacement)@nt[:3,:3].T+nt[:3,3]
        inverse=np.linalg.inv(t);local=points@inverse[:3,:3].T+inverse[:3,3]
        for vertex,point in zip(replacement.find(tag('vertices')),local):
            for key,value in zip(('x','y','z'),point):vertex.set(key,format(float(value),'.12g'))
        parent=next(o for o in child.find(tag('resources')) if o.find(tag('mesh')) is oldmesh)
        parent.remove(oldmesh);parent.append(replacement);files[path]=xml(child);changed.append(path)
        name=f'V{i} A2L hammered veneer and wall cradle r5'
        setmeta(obj,'name',name);setmeta(obj.find('part'),'name',name)
        count=str(len(replacement.find(tag('triangles'))))
        obj.find('part/mesh_stat').set('face_count',count)
        for meta in obj.findall('metadata'):
            if 'face_count' in meta.attrib:meta.set('face_count',count)
        setmeta(plate,'plater_name',f'{number} - {name}')
        files['Metadata/model_settings.config']=xml(cfg)
    allowed=set(changed)|{'Metadata/model_settings.config'}
    assert all(files[n]==v for n,v in original.items() if n not in allowed)
    write(target,files)
    return dict(source_sha256=sha(source),target_sha256=sha(target),changed_child_assets=changed,
                saved_transforms_and_global_settings_byte_preserved=True)


def build():
    assert sha(BASE/'Dara.3mf')==EXPECTED_SOURCE
    evidence=dict(revision=REVISION,editable=patch(BASE/OUT.relative_to(ROOT)/'Dara-A2L-Editable.3mf',EDIT),
        native=patch(BASE/'Dara.3mf',WORK/'wall-cradle-native.3mf'))
    save_json(WORK/'geometry-patch.json',evidence)
    print('Replaced only the three veneer mesh assets; saved settings and poses retained.',flush=True)


def slice_plate(number):
    folder=WORK/f'plate-{number}';folder.mkdir(exist_ok=True)
    for attempt in range(3):
        with (folder/'cli.log').open('w') as log:
            result=subprocess.run([str(EXE),'--slice',str(number),'--export-3mf','sliced.3mf','--outputdir',str(folder),str(EDIT)],
                cwd=EXE.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode!=3221225477:break
        print(f'Retrying Studio startup for plate {number}',flush=True)
    result.check_returncode()
    data=json.loads((folder/'result.json').read_text());assert data['return_code']==0
    assert [p['id'] for p in data['sliced_plates']]==[number]
    print(f"Plate {number}: {sum(f['total_used_g'] for f in data['sliced_plates'][0]['filaments']):.2f} g",flush=True)


def merge():
    files=read(WORK/'wall-cradle-native.3mf')
    cfg=ET.fromstring(files['Metadata/model_settings.config']);info=ET.fromstring(files['Metadata/slice_info.config'])
    seq=json.loads(files['Metadata/filament_sequence.json'])
    result=copy.deepcopy(json.loads((BASE/OUT.relative_to(ROOT)/'native-validation.json').read_text())['slicer_result'])
    for number in sorted(CHANGED):
        folder=WORK/f'plate-{number}';one=read(folder/'sliced.3mf')
        assert json.loads(one['Metadata/project_settings.config'])==json.loads(files['Metadata/project_settings.config'])
        sc=ET.fromstring(one['Metadata/model_settings.config']);fp=cfg.findall('plate')[number-1];sp=sc.findall('plate')[number-1]
        foid=props(fp.find('model_instance'))['object_id'];soid=props(sp.find('model_instance'))['object_id']
        assert props(cfg.find(f"object[@id='{foid}']"))==props(sc.find(f"object[@id='{soid}']"))
        replacement=copy.deepcopy(sp);setmeta(replacement.find('model_instance'),'object_id',foid)
        index=list(cfg).index(fp);cfg.remove(fp);cfg.insert(index,replacement)
        si=ET.fromstring(one['Metadata/slice_info.config'])
        old=next(p for p in info.findall('plate') if props(p)['index']==str(number))
        new=next(p for p in si.findall('plate') if props(p)['index']==str(number))
        index=list(info).index(old);info.remove(old);info.insert(index,copy.deepcopy(new))
        seq[f'plate_{number}']=json.loads(one['Metadata/filament_sequence.json'])[f'plate_{number}']
        assets={n:v for n,v in one.items() if plate_asset(n,number)}
        assert f'Metadata/plate_{number}.gcode' in assets
        files.update(assets)
        result['sliced_plates'][number-1]=json.loads((folder/'result.json').read_text())['sliced_plates'][0]
    files['Metadata/model_settings.config']=xml(cfg);files['Metadata/slice_info.config']=xml(info)
    files['Metadata/filament_sequence.json']=json.dumps(seq).encode()
    write(NATIVE/'sliced.3mf',files);save_json(NATIVE/'result.json',result)
    print('Merged three native veneer plates; other plate assets preserved.',flush=True)


def plate_asset(name,number):
    return re.fullmatch(rf'Metadata/(?:plate_{number}(?:_small)?|plate_no_light_{number}|top_{number}|pick_{number})\.(?:png|json|gcode(?:\.md5)?)',name)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['snapshot','build','slice','merge']);parser.add_argument('--plate',type=int,choices=[15,16,17]);args=parser.parse_args()
    if args.action=='slice':
        for number in ([args.plate] if args.plate else sorted(CHANGED)):slice_plate(number)
    else:{'snapshot':snapshot,'build':build,'merge':merge}[args.action]()
