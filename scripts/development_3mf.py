"""Small editable development projects, using the release's printer/materials.

Meshes and poses are supplied in assembly coordinates. No release file is edited.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import trimesh
from build_jointed_bambu_project import C, P, R, IDENTITY, tag, uid, meta, xml, model
from colorize_print_project import read_mesh
from validate_print_project import props, transform

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/development/m-veneer-cosmetic-fit'
WORK = ROOT / '.work/m-veneer-cosmetic-fit'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_path():
    baseline=ROOT/'reference/production/Dara-Solid-M-Baseline.3mf'
    return baseline if baseline.exists() else ROOT/'Dara.3mf'


def source():
    with zipfile.ZipFile(source_path()) as z:
        return {n: z.read(n) for n in z.namelist()}


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def solid(mesh):
    import manifold3d as mf
    # Join exact duplicated property vertices without moving any coordinates.
    v, inv = np.unique(mesh.vertices, axis=0, return_inverse=True)
    f = inv[mesh.faces]
    f = f[(f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])]
    m = mf.Manifold(mf.Mesh64(v, f.astype(np.uint64)))
    if m.status() != mf.Error.NoError:
        clean = trimesh.Trimesh(v, f, process=True)
        m = mf.Manifold(mf.Mesh64(clean.vertices, clean.faces.astype(np.uint64)))
    assert m.status() == mf.Error.NoError, m.status()
    return m


def mesh(m):
    raw = m.to_mesh64()
    # Manifold carries explicit property-vertex joins. Generic rounded merging
    # can collapse the very small triangles at clipped height-field boundaries.
    parents=np.arange(len(raw.vert_properties))
    def root(i):
        while parents[i]!=i:
            parents[i]=parents[parents[i]];i=parents[i]
        return i
    for a,b in zip(raw.merge_from_vert,raw.merge_to_vert):parents[root(int(a))]=root(int(b))
    ids=np.array([root(i) for i in range(len(parents))]);used,inv=np.unique(ids,return_inverse=True)
    f=inv[raw.tri_verts]
    valid=(f[:,0]!=f[:,1])&(f[:,1]!=f[:,2])&(f[:,0]!=f[:,2])
    result = trimesh.Trimesh(raw.vert_properties[used], f[valid], process=False)
    assert result.is_volume, (result.is_watertight, result.volume)
    return result


def centered(m, rotation=None, z=0, xy=(128, 128)):
    t = np.eye(4)
    if rotation is not None:
        t[:3, :3] = np.asarray(rotation)[:3, :3]
    v = m.vertices @ t[:3, :3].T
    t[:2, 3] = np.asarray(xy) - (v.min(axis=0)[:2] + v.max(axis=0)[:2]) / 2
    t[2, 3] = z - v[:, 2].min()
    return t


def z_rotation(deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def common_m_rotation():
    # Exact saved M5 orientation; same assembled layer planes on every face.
    a = np.radians(55); c, s = np.cos(a), np.sin(a)
    return np.array([[-c, 0, s], [0, -1, 0], [s, 0, c]])


def read_object(files, oid):
    root = ET.fromstring(files['3D/3dmodel.model'])
    cfg = ET.fromstring(files['Metadata/model_settings.config'])
    obj = root.find(tag('resources')).find(f"{tag('object')}[@id='{oid}']")
    config = cfg.find(f"object[@id='{oid}']")
    components = {c.get('objectid'): c for c in obj.find(tag('components'))}
    result = []
    for part in config.findall('part'):
        co = components[part.get('id')]
        path = co.get('{' + P + '}path').lstrip('/')
        child = ET.fromstring(files[path])
        m = read_mesh(child.find(tag('resources')).find(f"{tag('object')}[@id='{part.get('id')}']"))
        m.apply_transform(transform(co.get('transform')))
        result.append(dict(mesh=m, subtype=part.get('subtype'), settings=props(part)))
    return result, props(config)


def mesh_xml(resources, pid, m, block_front=False):
    obj = ET.SubElement(resources, tag('object'), id=str(pid), type='model')
    body = ET.SubElement(obj, tag('mesh'))
    vs = ET.SubElement(body, tag('vertices'))
    for v in m.vertices:
        ET.SubElement(vs, tag('vertex'), **dict(zip(('x', 'y', 'z'), (format(float(x), '.12g') for x in v))))
    fs = ET.SubElement(body, tag('triangles'))
    normals = m.face_normals if block_front else None
    for i, f in enumerate(m.faces):
        attrs = dict(zip(('v1', 'v2', 'v3'), map(str, f)))
        if block_front and normals[i, 2] > .01:
            attrs['paint_supports'] = '8'  # native support blocker, decorative face
        ET.SubElement(fs, tag('triangle'), **attrs)


def write_project(path, plates, title, settings_update=None):
    """plates = lists of {name, parts, transform, settings}; no stale gcode."""
    original = source()
    settings = json.loads(original['Metadata/project_settings.config'])
    settings.update(print_settings_id=title, print_sequence='by layer')
    settings.update(settings_update or {})
    files = {'[Content_Types].xml': original['[Content_Types].xml'],
             '_rels/.rels': b'<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>',
             'Metadata/project_settings.config': json.dumps(settings, indent=2).encode()}
    root = model(); del root.attrib['xmlns:p']
    for k, v in [('Application', 'BambuStudio-02.08.02.61'), ('BambuStudio:3mfVersion', '1'),
                 ('Title', title), ('Description', 'Development candidate. Physical fit and finish confirmation required.')]:
        ET.SubElement(root, tag('metadata'), name=k).text = v
    resources = ET.SubElement(root, tag('resources'))
    build = ET.SubElement(root, tag('build'), attrib={'{' + P + '}UUID': uid()})
    cfg = ET.Element('config'); rels = ET.Element('Relationships', xmlns=R)
    records = []; next_id = 1000; columns=math.ceil(math.sqrt(len(plates)))
    for pi, objects in enumerate(plates):
        plate = ET.SubElement(cfg, 'plate')
        for k, v in [('plater_id', pi + 1), ('plater_name', f'{pi + 1} - {objects[0]["name"]}'),
                     ('locked', 'false'), ('filament_map_mode', 'Auto For Flush'),
                     ('filament_maps', '1 1 1 1'), ('filament_volume_maps', '0 0 0 0')]:
            meta(plate, k, v)
        for entry in objects:
            oid = entry.get('object_id',next_id); next_id = max(next_id,oid)+100
            top = ET.SubElement(resources, tag('object'), id=str(oid), type='model', attrib={'{' + P + '}UUID': uid()})
            comps = ET.SubElement(top, tag('components'))
            co = ET.SubElement(cfg, 'object', id=str(oid))
            for k, v in {**entry.get('settings', {}), 'name': entry['name']}.items():
                if k is not None and v is not None: meta(co, k, v)
            child = model(); child_res = ET.SubElement(child, tag('resources'))
            child_path = f'3D/Objects/{oid}.model'
            for j, part in enumerate(entry['parts'], 1):
                pid = oid + j
                mesh_xml(child_res, pid, part['mesh'], entry.get('block_front', False) and part.get('subtype', 'normal_part') == 'normal_part')
                ET.SubElement(comps, tag('component'), objectid=str(pid), transform=IDENTITY,
                              attrib={'{' + P + '}path': '/' + child_path, '{' + P + '}UUID': uid()})
                pc = ET.SubElement(co, 'part', id=str(pid), subtype=part.get('subtype', 'normal_part'))
                for k, v in {'name': entry['name'] if j == 1 else 'Modifier', **part.get('settings', {})}.items():
                    if k is not None and v is not None and k not in ('matrix', 'source_file', 'source_object_id', 'source_volume_id', 'source_offset_x', 'source_offset_y', 'source_offset_z'):
                        meta(pc, k, v)
                ET.SubElement(pc, 'mesh_stat', face_count=str(len(part['mesh'].faces)), edges_fixed='0', degenerate_facets='0', facets_removed='0', facets_reversed='0', backwards_edges='0')
            files[child_path] = xml(child)
            ET.SubElement(rels, 'Relationship', Target='/' + child_path, Id=f'rel-{oid}', Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
            local = np.asarray(entry['transform']); t = local.copy()
            t[:2, 3] += [pi % columns * 307.2, -(pi // columns) * 307.2]
            ET.SubElement(build, tag('item'), objectid=str(oid), printable='1', transform=' '.join(format(float(x), '.12g') for x in t[:3].T.reshape(-1)), attrib={'{' + P + '}UUID': uid()})
            inst = ET.SubElement(plate, 'model_instance')
            for k, v in [('object_id', oid), ('instance_id', 0), ('identify_id', oid)]: meta(inst, k, v)
            v = entry['parts'][0]['mesh'].vertices @ local[:3, :3].T + local[:3, 3]
            records.append(dict(name=entry['name'], plate=pi + 1, object_id=oid, assembly_to_printer=local.tolist(), body_bounds_mm=[v.min(axis=0).tolist(), v.max(axis=0).tolist()]))
    files.update({'3D/3dmodel.model': xml(root), '3D/_rels/3dmodel.model.rels': xml(rels), 'Metadata/model_settings.config': xml(cfg)})
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, content in files.items(): z.writestr(n, content)
    save_json(path.with_suffix('.json'), dict(title=title, source_sha256=sha(source_path()), records=records, native_slice_validated=False, physical_confirmation_pending=True))
    return records
