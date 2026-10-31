"""Move B1/B3 keyholes to the opposite ends, retaining upward slot direction.

Revision-specific migration of saved production meshes; never regenerate the
knot, locating keys, attachment bores or unrelated accessories.
"""
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / '.work/python-libs'), str(ROOT / 'scripts')]
import numpy as np
import manifold3d as mf
from development_3mf import solid, mesh, mesh_xml, props, tag, transform, P
from organize_root_projects import rows, sha, dump, ASSET, matrix_text, BOOKKEEPING
from promote_veneer_wall_cradle import read, write, EXE, setmeta

WORK = ROOT / '.work/wall-keyholes-r1'
REPORT = ROOT / 'release/wall-keyholes-r1'
BASE = WORK / 'before.3mf'
EDIT = WORK / 'editable.3mf'
FINAL = WORK / 'final.3mf'
NAMES = {'B1 A1 companion wall block', 'B3 A1 companion wall block'}


def build():
    WORK.mkdir(parents=True, exist_ok=True)
    REPORT.mkdir(parents=True, exist_ok=True)
    if not BASE.exists():
        shutil.copyfile(ROOT / 'Small Parts.3mf', BASE)
    assert sha(BASE) == sha(ROOT / 'Small Parts.3mf'), 'Build requires original production baseline; use finish to restore the validated revision.'
    files = read(BASE)
    cfg = ET.fromstring(files['Metadata/model_settings.config'])
    model = ET.fromstring(files['3D/3dmodel.model'])
    _, objects = rows(BASE)
    records = []
    for obj in objects:
        if obj['name'] not in NAMES:
            continue
        old = solid(obj['parts'][0]['mesh'])
        # Extract the exact original cavity, including entry, lip and head
        # channel. This bounded region contains no other openings or keys.
        region = mf.Manifold.cube((12, 24, 10)).translate((45, -11, 0))
        cavity = region - old
        assert np.allclose(mesh(cavity).bounds, [[46.5,-9.5,0],[55.5,10.5,7]])
        newx = -51
        moved = cavity.translate((-102, 0, 0))
        new = (old + cavity) - moved
        assert abs(new.volume() - old.volume()) < 1e-6
        # Symmetric differences must consist only of the old and new cavity.
        assert abs((new-old).volume()-cavity.volume()) < 1e-6
        assert abs((old-new).volume()-cavity.volume()) < 1e-6
        assert ((new-old)-cavity).volume() < 1e-6
        assert ((old-new)-moved).volume() < 1e-6
        normal = mesh(new)
        assert normal.is_volume
        node = next(o for o in cfg.findall('object') if props(o)['name'] == obj['name'])
        parent = model.find(tag('resources')).find(f"{tag('object')}[@id='{node.get('id')}']")
        components = {c.get('objectid'): c for c in parent.find(tag('components'))}
        part = node.findall('part')[0]
        co = components[part.get('id')]
        path = co.get('{' + P + '}path').lstrip('/')
        local = normal.copy()
        local.apply_transform(np.linalg.inv(transform(co.get('transform'))))
        tree = ET.fromstring(files[path])
        resource = tree.find(tag('resources'))
        oldnode = resource.find(f"{tag('object')}[@id='{part.get('id')}']")
        assert all(set(t.attrib) == {'v1','v2','v3'} for t in oldnode.findall('.//' + tag('triangle')))
        temp = ET.Element(tag('resources'))
        mesh_xml(temp, part.get('id'), local)
        oldnode.remove(oldnode.find(tag('mesh')))
        oldnode.append(temp[0].find(tag('mesh')))
        # Preserve every other object in the asset byte for byte.
        source = files[path].decode()
        replacement = ET.tostring(oldnode, encoding='unicode')
        source, count = re.subn(rf'<object\b[^>]*\bid="{part.get("id")}"[^>]*>.*?</object>', lambda _: replacement, source, flags=re.S)
        assert count == 1
        files[path] = source.encode()
        reinforcement = node.findall('part')[3]
        assert props(reinforcement)['name'] == '100% wall keyhole seat and lip'
        co = components[reinforcement.get('id')]
        t = transform(co.get('transform'))
        t[0,3] = newx
        co.set('transform', matrix_text(t))
        # Saved source bookkeeping uses doubled center coordinates here.
        mat = np.array([float(v) for v in props(reinforcement)['matrix'].split()]).reshape(4,4)
        mat[:3,:3] = t[:3,:3]; mat[0,3] = 2*newx
        setmeta(reinforcement, 'matrix', ' '.join(format(v,'.12g') for v in mat.ravel()))
        records.append(dict(block=obj['name'],keyhole_x_before_mm=51,keyhole_x_after_mm=newx,
                            keyhole_rotation_degrees=0,
                            narrow_seat_direction='Photo top / artwork top / model +Y',
                            cavity_volume_mm3=cavity.volume(),watertight=True,
                            attachment_bores_and_keys_preserved=True,solid_difference_confined_to_keyholes=True))
    assert len(records) == 2
    files['3D/3dmodel.model'] = ET.tostring(model, encoding='utf-8', xml_declaration=True)
    files['Metadata/model_settings.config'] = ET.tostring(cfg, encoding='utf-8', xml_declaration=True)
    write(EDIT, files)
    dump(REPORT / 'geometry.json', dict(source_sha256=sha(BASE), changes=records,
         protected_projects={p.name:sha(p) for p in ROOT.glob('*.3mf') if p.name != 'Small Parts.3mf'}))


def native(source, folder, slice_plate=False):
    folder.mkdir(parents=True, exist_ok=True)
    args = ['--slice','3','--export-3mf','sliced.3mf'] if slice_plate else ['--info']
    for attempt in range(3):
        with (folder/'run.log').open('w') as log:
            p = subprocess.run([str(EXE), *args, '--outputdir',str(folder),str(source)],
                cwd=EXE.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        if p.returncode != 3221225477:
            break
    p.check_returncode()
    result = json.loads((folder/'result.json').read_text())
    assert result['return_code'] == 0
    return result


def finish():
    full = read(EDIT); sliced = read(WORK/'native/sliced.3mf')
    assert json.loads(full['Metadata/project_settings.config']) == json.loads(sliced['Metadata/project_settings.config'])
    settings, objects = rows(EDIT); _, native_objects = rows(WORK/'native/sliced.3mf')
    expected = {o['name']:o for o in objects if o['plate'] == 3}
    actual = {o['name']:o for o in native_objects}
    assert set(actual) == set(expected)
    from scipy.spatial import cKDTree
    for name, a in expected.items():
        b = actual[name]
        assert np.allclose(a['transform'], b['transform'], atol=1e-5)
        assert {k:v for k,v in a['settings'].items() if k not in BOOKKEEPING} == {k:v for k,v in b['settings'].items() if k not in BOOKKEEPING}
        assert len(a['parts']) == len(b['parts'])
        for x,y in zip(a['parts'],b['parts']):
            assert {k:v for k,v in x['settings'].items() if k not in BOOKKEEPING} == {k:v for k,v in y['settings'].items() if k not in BOOKKEEPING}
            assert cKDTree(x['mesh'].vertices).query(y['mesh'].vertices)[0].max() < 1e-4
            assert cKDTree(y['mesh'].vertices).query(x['mesh'].vertices)[0].max() < 1e-4
    for name,data in sliced.items():
        match = ASSET.fullmatch(name)
        if match and match[1] == '3':
            full[name] = data
    key = 'Metadata/slice_info.config'
    a,b = ET.fromstring(full[key]),ET.fromstring(sliced[key])
    old = next(p for p in a.findall('plate') if props(p)['index']=='3')
    new = next(p for p in b.findall('plate') if props(p)['index']=='3')
    i = list(a).index(old); a.remove(old);a.insert(i,copy.deepcopy(new))
    full[key] = ET.tostring(a,encoding='utf-8',xml_declaration=True)
    key = 'Metadata/filament_sequence.json'
    if key in sliced:
        a,b = json.loads(full[key]),json.loads(sliced[key]);a['plate_3']=b['plate_3'];full[key]=json.dumps(a).encode()
    write(FINAL,full)
    before=read(BASE)
    for i in [1,2,4,5]:
        assert full[f'Metadata/plate_{i}.gcode'] == before[f'Metadata/plate_{i}.gcode']
    _, oldobjects=rows(BASE)
    for a,b in zip(oldobjects,objects):
        assert a['name']==b['name'] and np.array_equal(a['transform'],b['transform'])
        assert a['settings']==b['settings']
        for i,(x,y) in enumerate(zip(a['parts'],b['parts'])):
            if a['name'] in NAMES and i in [0,3]: continue
            assert np.array_equal(x['mesh'].vertices,y['mesh'].vertices)
            assert np.array_equal(x['mesh'].faces,y['mesh'].faces)
            assert x['settings']==y['settings']
    native(FINAL,WORK/'reopen')
    geometry=json.loads((REPORT/'geometry.json').read_text())
    for name,digest in geometry['protected_projects'].items(): assert sha(ROOT/name)==digest
    shutil.copyfile(FINAL,ROOT/'Small Parts.3mf')
    # Refresh only this project's CAD/catalog entry, retaining other releases.
    import organize_root_projects as org
    original=json.loads((org.REPORT/'catalog.json').read_text())
    org.TITLES=['Small Parts'];org.export_cad()
    updated=json.loads((org.REPORT/'catalog.json').read_text())
    original.update(updated);dump(org.REPORT/'catalog.json',original)
    hashes=json.loads((org.REPORT/'gcode-sha256.json').read_text())
    hashes['Small Parts']={f'plate_{i}':hashlib.sha256(full[f'Metadata/plate_{i}.gcode']).hexdigest() for i in range(1,6)}
    dump(org.REPORT/'gcode-sha256.json',hashes)
    for folder in ['native','reopen']:
        for name in ['result.json','run.log']:
            shutil.copyfile(WORK/folder/name,REPORT/f'{folder}-{name}')
    result=json.loads((WORK/'native/result.json').read_text())
    dump(REPORT/'validation.json',dict(project_sha256=sha(FINAL),native_reopen=True,
         native_plate=3,other_plate_gcode_byte_identical=[1,2,4,5],
         unrelated_geometry_settings_and_poses_preserved=True,global_settings_byte_identical=True,
         slice_result=result,physical_qualification='Not yet printed'))
    print('Published corrected Small Parts.3mf; native plate 3 and reopen passed.')


def verify_and_preview():
    from PIL import Image, ImageDraw, ImageFont
    files=read(ROOT/'Small Parts.3mf')
    settings,objects=rows(ROOT/'Small Parts.3mf')
    locked=dict(sparse_infill_density='8%',sparse_infill_pattern='gyroid',layer_height='0.2',
        initial_layer_print_height='0.2',wall_loops='4',top_shell_layers='5',bottom_shell_layers='5',
        curr_bed_type='Textured PEI Plate',nozzle_diameter=['0.4'])
    for k,v in locked.items(): assert settings[k]==v
    cfg=ET.fromstring(files['Metadata/model_settings.config'])
    plate=next(p for p in ET.fromstring(files['Metadata/slice_info.config']).findall('plate') if props(p)['index']=='3')
    assert {p.get('identify_id') for p in plate.findall('object')} == {props(i)['identify_id'] for i in cfg.findall('plate')[2].findall('model_instance')}
    assert hashlib.md5(files['Metadata/plate_3.gcode']).hexdigest() == files['Metadata/plate_3.gcode.md5'].decode().strip().lower()
    img=Image.new('RGB',(1440,650),'#f4f5f7');draw=ImageDraw.Draw(img)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',25)
    title=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',32)
    draw.text((35,22),'Corrected mounting blocks — photo top is artwork top',font=title,fill='#182538')
    draw.text((35,65),'Only the right-hand pair changes. All narrow keyhole seats remain upward.',font=font,fill='#35465a')
    for name,cx,cy,label in [('B2',365,230,'Upper left: B2 — unchanged'),('B1',1070,230,'Upper right: B1 — corrected'),
                           ('B4',365,470,'Lower left: B4 — unchanged'),('B3',1070,470,'Lower right: B3 — corrected')]:
        obj=next(o for o in objects if o['name'].startswith(name+' '))
        section=obj['parts'][0]['mesh'].section(plane_origin=[0,0,0.1],plane_normal=[0,0,1])
        loops=sorted(section.discrete,key=lambda p:np.ptp(p[:,0])*np.ptp(p[:,1]),reverse=True)
        for i,loop in enumerate(loops):
            pts=[(cx-x*4.4,cy-y*4.4) for x,y,z in loop]
            draw.polygon(pts,fill='#dce3ec' if i==0 else '#f4f5f7');draw.line(pts,fill='#33465e',width=2)
        draw.text((cx-300,cy-125),label,font=font,fill='#182538')
        x=-51 if name in ['B1','B3'] else 51
        px=cx-x*4.4
        draw.ellipse((px-29,cy-52,px+29,cy+52),outline='#07845e' if name in ['B1','B3'] else '#718096',width=3)
    draw.text((35,600),'Green: relocated keyholes and reinforcement. Attachment holes and keys preserved.',font=font,fill='#08684c')
    img.save(REPORT/'corrected-blocks.png')
    report=json.loads((REPORT/'validation.json').read_text())
    report.update(locked_settings_verified=locked,native_gcode_md5_verified=True,slice_object_identifiers_verified=True)
    dump(REPORT/'validation.json',report)
    print('Locked constants, object identifiers and native G-code checksum verified.')


if __name__ == '__main__':
    action=sys.argv[1]
    if action=='build': build()
    elif action=='slice': native(EDIT,WORK/'native',True)
    elif action=='finish': finish()
    elif action=='verify': verify_and_preview()
