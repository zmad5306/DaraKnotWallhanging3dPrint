"""Package the approved print revisions without changing their geometry/settings.

Historical migration inputs are recorded in release/root-projects/sources.json.
Run `audit_root_projects.py` to validate a normal checkout; migration inputs are
intentionally no longer tracked. No command here sends a printer job.
"""
import argparse
import copy
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / '.work/python-libs'), str(ROOT / 'scripts')]
import numpy as np
from development_3mf import props, tag, transform, xml, P, R
from promote_veneer_wall_cradle import read, write, setmeta, EXE
from colorize_print_project import read_mesh

WORK = ROOT / '.work/root-projects'
REPORT = ROOT / 'release/root-projects'
TITLES = ['Knot', 'Letter', 'Small Parts', 'Small Parts - Crate Clips PETG',
          'Small Parts - Photo Cut Aligner', 'Small Parts - Sanding Block PLA',
          'Small Parts - Crate Stencils']
BOOKKEEPING = {'name', 'matrix', 'source_file', 'source_object_id', 'source_volume_id',
               'source_offset_x', 'source_offset_y', 'source_offset_z', None, 'null'}
ASSET = re.compile(r'Metadata/(?:plate_|plate_no_light_|top_|pick_)(\d+)(?:_small)?\.(?:png|json|gcode(?:\.md5)?)$')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def pitch(settings):
    a = np.array([[float(x) for x in q.split('x')] for q in settings['printable_area']])
    return np.ptp(a, axis=0) * 1.2


def grid(i, count, spacing):
    cols = math.ceil(math.sqrt(count))
    return np.array([i % cols, -(i // cols)]) * spacing


def matrix_text(t):
    return ' '.join(format(float(v), '.15g') for v in t[:3].T.reshape(-1))


def clean_relations(files):
    for name in [n for n in files if n.endswith('.rels')]:
        root = ET.Element('Relationships', xmlns=R)
        for rel in ET.fromstring(files[name]):
            if rel.get('TargetMode') == 'External' or rel.get('Target').lstrip('/') in files:
                ET.SubElement(root, 'Relationship', rel.attrib)
        files[name] = xml(root)


def extract_letter(source, dest):
    files = read(source)
    cfg = ET.fromstring(files['Metadata/model_settings.config'])
    model = ET.fromstring(files['3D/3dmodel.model'])
    settings = json.loads(files['Metadata/project_settings.config'])
    oldplates = cfg.findall('plate')
    retained = oldplates[10:17]
    mapping = {i+11:i+1 for i in range(7)}
    ids = {props(ins)['object_id']:i for i,p in enumerate(retained) for ins in p.findall('model_instance')}
    assets = set()
    resources = model.find(tag('resources'))
    for obj in list(resources):
        if obj.get('id') not in ids:
            resources.remove(obj)
        else:
            assets.update(c.get('{' + P + '}path').lstrip('/') for c in obj.find(tag('components')))
    for obj in cfg.findall('object'):
        if obj.get('id') not in ids: cfg.remove(obj)
    for p in oldplates:
        if p not in retained: cfg.remove(p)
    for i,p in enumerate(retained):
        setmeta(p, 'plater_id', i+1)
        setmeta(p, 'plater_name', re.sub(r'^\d+ - ', f'{i+1} - ', props(p)['plater_name']))
        for md in p.findall('metadata'):
            value = md.get('value', '')
            if ASSET.fullmatch(value):
                md.set('value', re.sub(r'_(\d+)(?=\.|_small)', lambda m:'_'+str(mapping[int(m[1])]), value))
    for it in list(model.find(tag('build'))):
        oid = it.get('objectid')
        if oid not in ids:
            model.find(tag('build')).remove(it)
        else:
            i=ids[oid];t=transform(it.get('transform'))
            t[:2,3] += grid(i,7,pitch(settings))-grid(i+10,20,pitch(settings))
            it.set('transform',matrix_text(t))
    for n in list(files):
        if n.startswith('3D/Objects/') and n not in assets: del files[n]
    renamed = {}
    for n in list(files):
        hit=ASSET.fullmatch(n)
        if hit:
            b=files.pop(n);old=int(hit[1])
            if old in mapping:
                renamed[re.sub(r'_(\d+)(?=\.|_small)', lambda m:'_'+str(mapping[int(m[1])]),n)] = b
    files.update(renamed)
    si=ET.fromstring(files['Metadata/slice_info.config'])
    for p in si.findall('plate'):
        old=int(props(p)['index'])
        if old not in mapping: si.remove(p)
        else: setmeta(p,'index',mapping[old])
    seq=json.loads(files['Metadata/filament_sequence.json'])
    files['Metadata/filament_sequence.json']=json.dumps({f'plate_{v}':seq[f'plate_{k}'] for k,v in mapping.items()}).encode()
    files['Metadata/slice_info.config']=xml(si)
    for k in ['wipe_tower_x','wipe_tower_y']: settings[k]=settings[k][10:17]
    files['Metadata/project_settings.config']=json.dumps(settings,indent=2).encode()
    files['Metadata/model_settings.config']=xml(cfg)
    files['3D/3dmodel.model']=xml(model)
    clean_relations(files)
    write(dest,files)
    original=read(source)
    for a,b in mapping.items():
        assert original[f'Metadata/plate_{a}.gcode']==files[f'Metadata/plate_{b}.gcode']
    return mapping


def combine_small(sources, dest):
    files=read(sources[0]);base=json.loads(files['Metadata/project_settings.config'])
    cfg=ET.fromstring(files['Metadata/model_settings.config']);model=ET.fromstring(files['3D/3dmodel.model'])
    cfg.clear();resources=model.find(tag('resources'));resources.clear();build=model.find(tag('build'));build.clear()
    for n in list(files):
        if n.startswith('3D/Objects/') or ASSET.fullmatch(n) or n in ['Metadata/slice_info.config','Metadata/filament_sequence.json','Metadata/cut_information.xml']:
            del files[n]
    plate_no=0;mapping=[];rels=ET.Element('Relationships',xmlns=R)
    for group,path in enumerate(sources):
        src=read(path);sc=ET.fromstring(src['Metadata/model_settings.config']);sm=ET.fromstring(src['3D/3dmodel.model'])
        # Studio uses UUIDs to share volumes, even across different asset paths.
        # Independently generated projects reuse these IDs; namespace each input.
        def unique_ids(tree):
            for node in tree.iter():
                for key,value in list(node.attrib.items()):
                    if key.endswith('UUID'):
                        node.set(key,str(uuid.uuid5(uuid.NAMESPACE_URL,f'dara-root-group-{group}/{value}')))
            return tree
        unique_ids(sm)
        ss=json.loads(src['Metadata/project_settings.config'])
        assert {k:v for k,v in ss.items() if k!='print_settings_id'}=={k:v for k,v in base.items() if k!='print_settings_id'}
        oldplates=sc.findall('plate');ids={}
        for old_i,p in enumerate(oldplates):
            newp=copy.deepcopy(p);setmeta(newp,'plater_id',plate_no+1)
            for md in list(newp.findall('metadata')):
                if md.get('key') in ['gcode_file','thumbnail_file','thumbnail_no_light_file','top_file','pick_file']:newp.remove(md)
            setmeta(newp,'plater_name',re.sub(r'^\d+ - ',f'{plate_no+1} - ',props(p)['plater_name']))
            for ins in newp.findall('model_instance'):
                old=props(ins)['object_id'];new=str(int(old)+group*10000)
                ids[old]=(new,old_i,plate_no)
                setmeta(ins,'object_id',new);setmeta(ins,'identify_id',int(props(ins)['identify_id'])+group*10000)
            cfg.append(newp);mapping.append(dict(source=str(path.relative_to(ROOT)),source_plate=old_i+1,plate=plate_no+1));plate_no+=1
        for obj in sc.findall('object'):
            new=copy.deepcopy(obj);new.set('id',ids[obj.get('id')][0])
            for part in new.findall('part'):
                part.set('id',str(int(part.get('id'))+group*10000))
                for md in part.findall('metadata'):
                    if md.get('key')=='shared_mesh_id' and int(md.get('value'))>=0:
                        md.set('value',str(int(md.get('value'))+group*10000))
            cfg.insert(0,new)
        for obj in sm.find(tag('resources')):
            new=copy.deepcopy(obj);new.set('id',ids[obj.get('id')][0])
            for c in new.find(tag('components')):
                old=c.get('{' + P + '}path').lstrip('/');newpath='3D/Objects/'+f'group{group}_'+Path(old).name
                c.set('{' + P + '}path','/'+newpath)
                c.set('objectid',str(int(c.get('objectid'))+group*10000))
                child=unique_ids(ET.fromstring(src[old]))
                for childobj in child.find(tag('resources')):
                    childobj.set('id',str(int(childobj.get('id'))+group*10000))
                files[newpath]=xml(child)
            resources.append(new)
        for it in sm.find(tag('build')):
            new=copy.deepcopy(it);oid,old_i,new_i=ids[it.get('objectid')];new.set('objectid',oid)
            t=transform(it.get('transform'));t[:2,3]+=grid(new_i,5,pitch(base))-grid(old_i,len(oldplates),pitch(base))
            new.set('transform',matrix_text(t));build.append(new)
    assert plate_no==5
    for i,n in enumerate(sorted(n for n in files if n.startswith('3D/Objects/'))):
        ET.SubElement(rels,'Relationship',Target='/'+n,Id=f'rel-{i}',Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
    ET.SubElement(cfg,'assemble')
    files['3D/_rels/3dmodel.model.rels']=xml(rels)
    files['Metadata/model_settings.config']=xml(cfg);files['3D/3dmodel.model']=xml(model)
    for k in ['wipe_tower_x','wipe_tower_y']:base[k]=[base[k][0]]*5
    files['Metadata/project_settings.config']=json.dumps(base,indent=2).encode()
    clean_relations(files);write(dest,files)
    return mapping


def rows(path):
    files=read(path);cfg=ET.fromstring(files['Metadata/model_settings.config']);model=ET.fromstring(files['3D/3dmodel.model'])
    settings=json.loads(files['Metadata/project_settings.config']);plates=cfg.findall('plate')
    objects={o.get('id'):o for o in model.find(tag('resources'))};configs={o.get('id'):o for o in cfg.findall('object')}
    items={o.get('objectid'):o for o in model.find(tag('build'))};assets={};result=[]
    for i,plate in enumerate(plates):
        for ins in plate.findall('model_instance'):
            oid=props(ins)['object_id'];t=transform(items[oid].get('transform'));t[:2,3]-=grid(i,len(plates),pitch(settings))
            components={c.get('objectid'):c for c in objects[oid].find(tag('components'))};parts=[]
            for part in configs[oid].findall('part'):
                co=components[part.get('id')];asset=co.get('{' + P + '}path').lstrip('/')
                if asset not in assets:
                    tree=ET.fromstring(files[asset]);assets[asset]={o.get('id'):o for o in tree.find(tag('resources'))}
                node=assets[asset][co.get('objectid')];mesh=read_mesh(node);mesh.apply_transform(transform(co.get('transform')))
                paint=[dict(x.attrib) for x in node.find(tag('mesh')).find(tag('triangles')) if len(x.attrib)>3]
                parts.append(dict(mesh=mesh,subtype=part.get('subtype'),settings=props(part),paint=paint))
            result.append(dict(name=props(configs[oid])['name'],id=oid,plate=i+1,transform=t,settings=props(configs[oid]),parts=parts))
    return settings,result


def compare(source,dest,plate_map=None):
    a,old=rows(source);b,new=rows(dest)
    if plate_map is not None:
        old=[r for r in old if r['plate'] in plate_map]
        for r in old:r['plate']=plate_map[r['plate']]
    assert len(old)==len(new),(source,len(old),len(new))
    changes={k:[a.get(k),b.get(k)] for k in set(a)|set(b) if a.get(k)!=b.get(k)}
    for key in ['different_settings_to_system','inherits_group','filament_map_2']:
        if key in changes:
            before,after=changes[key]
            assert before is None and isinstance(after,list)
            assert all(v==('1' if key=='filament_map_2' else '') for v in after)
    assert set(changes)<= {'wipe_tower_x','wipe_tower_y','different_settings_to_system','inherits_group','filament_map_2'},changes
    maxerr=0;bookkeeping_changes=[]
    for s,d in zip(old,new):
        assert (s['name'],s['plate'])==(d['name'],d['plate'])
        assert s['settings']==d['settings']
        assert np.max(np.abs(s['transform']-d['transform']))<.0001
        assert len(s['parts'])==len(d['parts'])
        for x,y in zip(s['parts'],d['parts']):
            differences={k:[x['settings'].get(k),y['settings'].get(k)] for k in set(x['settings'])|set(y['settings']) if x['settings'].get(k)!=y['settings'].get(k)}
            assert set(differences)<=BOOKKEEPING and x['subtype']==y['subtype'],differences
            if differences:bookkeeping_changes.append(dict(object=s['name'],changes=differences))
            assert x['paint']==y['paint']
            assert np.array_equal(x['mesh'].faces,y['mesh'].faces)
            e=float(np.max(np.abs(x['mesh'].vertices-y['mesh'].vertices)));maxerr=max(maxerr,e);assert e<.0001,e
    return dict(objects=len(new),max_vertex_difference_mm=maxerr,settings_changes=changes,paint_preserved=True,bed_poses_preserved=True,source_bookkeeping_changes=bookkeeping_changes)


def build():
    sources=json.loads((WORK/'sources.json').read_text())
    source_paths={k:ROOT/v for k,v in sources.items()}
    source_paths['Stencils']=WORK/'stencils/Christmas-Crate-Stencils.3mf'
    provenance={k:dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for k,p in source_paths.items()}
    dump(REPORT/'sources.json',provenance)
    for title,key in [('Knot','Knot'),(TITLES[3],'Crate'),(TITLES[4],'Photo'),(TITLES[5],'Sanding'),(TITLES[6],'Stencils')]:
        shutil.copyfile(source_paths[key],ROOT/(title+'.3mf'))
    lm=extract_letter(source_paths['Letter'],ROOT/'Letter.3mf')
    dump(REPORT/'letter-preservation.json',compare(source_paths['Letter'],ROOT/'Letter.3mf',lm))
    sm=combine_small([source_paths[k] for k in ['Small Parts','Center','Sides']],ROOT/'Small Parts.3mf')
    dump(REPORT/'plate-map.json',dict(Letter=lm,Small_Parts=sm))
    for title in TITLES:shutil.copyfile(ROOT/(title+'.3mf'),WORK/(title+'-before-slice.3mf'))
    print('Built seven root projects; protected inputs remain unchanged.',flush=True)


def native(title, slice_it):
    out=WORK/'native'/title;out.mkdir(parents=True,exist_ok=True)
    cmd=[str(EXE),'--slice','0','--export-3mf','sliced.3mf'] if slice_it else [str(EXE),'--info']
    cmd+=['--outputdir',str(out),str(ROOT/(title+'.3mf'))]
    for attempt in range(3):
        with (out/'run.log').open('w') as log:
            p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        if p.returncode==0:break
        if p.returncode!=3221225477:break
    assert p.returncode==0,(title,p.returncode)
    if slice_it:
        # Native normalization may rename source bookkeeping only. Inspect before promotion.
        check=compare(ROOT/(title+'.3mf'),out/'sliced.3mf')
        shutil.copyfile(out/'sliced.3mf',ROOT/(title+'.3mf'))
        dump(REPORT/(title+'-slice-preservation.json'),check)
    shutil.copyfile(out/'run.log',REPORT/(title+'-native.log'))
    result=out/'result.json'
    if result.exists():shutil.copyfile(result,REPORT/(title+'-native.json'))
    print(title,'native slice' if slice_it else 'native reopen','passed',flush=True)


def export_cad():
    catalog={}
    for title in TITLES:
        st,objects=rows(ROOT/(title+'.3mf'));folder=ROOT/(title+' STL');folder.mkdir(exist_ok=True)
        lines=['// Exact mesh-based CAD snapshot of '+title+'.3mf.',
               '// Uses the supplied STL volumes; this is not a parametric feature history.',
               '// Dimensions, material regions, print poses and modifiers come from the saved project.',
               'plate = 1; // Select the plate to inspect. 0 shows all plates.',
               'show_modifiers = false;','']
        records=[];dedup={}
        for obj in objects:
            partrows=[]
            for i,part in enumerate(obj['parts']):
                data=part['mesh'].export(file_type='stl');digest=hashlib.sha256(data).hexdigest()
                if digest not in dedup:
                    slug=re.sub(r'[^A-Za-z0-9_-]+','-',obj['name']).strip('-')[:65]
                    name=f'{slug}-volume-{i+1}.stl';(folder/name).write_bytes(data);dedup[digest]=name
                name=dedup[digest];normal=part['subtype']=='normal_part'
                filament=int(part['settings'].get('extruder',obj['settings'].get('extruder','1')))
                color=st['filament_colour'][max(0,filament-1)] if normal else '#FF00FF'
                t=obj['transform'].copy();offset=grid(obj['plate']-1,len({r['plate'] for r in objects}),pitch(st))
                lines += [f'// Plate {obj["plate"]}: {obj["name"]}; volume {i+1}; {part["subtype"]}',
                    f'if ((plate == 0 || plate == {obj["plate"]})'+(')' if normal else ' && show_modifiers)'),
                    f' translate(plate == 0 ? {json.dumps([float(offset[0]),float(offset[1]),0])} : [0,0,0])',
                    f'  multmatrix({json.dumps(t.tolist())})',
                    f'   color("{color}") import("{title} STL/{name}", convexity=20);','']
                partrows.append(dict(file=(folder/name).relative_to(ROOT).as_posix(),sha256=digest,subtype=part['subtype'],settings=part['settings'],faces=len(part['mesh'].faces),bounds=part['mesh'].bounds.tolist()))
            records.append(dict(name=obj['name'],plate=obj['plate'],transform=obj['transform'].tolist(),settings=obj['settings'],parts=partrows))
        cad=ROOT/(title+'.scad');cad.write_text('\n'.join(lines).rstrip()+'\n',encoding='utf-8',newline='\n')
        catalog[title]=dict(project=title+'.3mf',sha256=sha(ROOT/(title+'.3mf')),cad=cad.name,cad_sha256=sha(cad),printer=st['printer_model'],plates=len({r['plate'] for r in objects}),objects=records,unique_stl=len(dedup))
        print(title, len(objects),'objects,',len(dedup),'unique STL volumes',flush=True)
    dump(REPORT/'catalog.json',catalog)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','native','cad']);p.add_argument('--title');p.add_argument('--slice',action='store_true');args=p.parse_args()
    if args.action=='build':build()
    elif args.action=='native':native(args.title,args.slice)
    else:export_cad()
