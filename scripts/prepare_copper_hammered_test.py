"""Build, slice and audit one domed face with concave hammered dimples."""
import argparse
import json
import math
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from build_jointed_bambu_project import P, R, IDENTITY, meta, mesh_object, model, tag, uid, trimesh, np
from tune_silk_project import OBJECT_SETTINGS, read_zip, write_zip, props, setmeta, sha, xml
from prepare_copper_diagnostic_test import inspect_moves
from validate_print_project import scan_gcode, nearest_error, transform
from mesh_sections import mesh_slice

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.work/copper-hammered-v4-crowned-dimples'
TARGET = ROOT / 'Dara-Copper-Hammered-Test.3mf'
REPORT = ROOT / 'working/bambu/Dara-Photo-Frame-A1-Jointed/copper-hammered-test.json'
PREVIEW = ROOT / 'output/renderings/copper-texture-concepts-2026-10-14/actual-coupon-geometry.png'
TITLE = 'Copper domed face with hammered dimples - 25 mm coupon'
BASE_HEIGHT = 4.0
CROWN_RISE = 2.0
DIMPLE_DEPTH = .6
BORDER_WIDTH = .5
OVERRIDES = dict(OBJECT_SETTINGS, name='H - one domed face with concave dimples - 25 x 25 mm', extruder='3',
                 enable_support='0', brim_type='no_brim', sparse_infill_density='15%', sparse_infill_pattern='gyroid')


def surface_fields(xx, yy, cells):
    """One broad crown with only subtractive indentations, fading at its edge."""
    half_face = 12.5 - BORDER_WIDTH
    crown = CROWN_RISE * np.maximum(0, 1 - (xx / half_face) ** 2) * np.maximum(0, 1 - (yy / half_face) ** 2)
    depression = np.zeros_like(crown)
    for cell in cells:
        dx, dy = xx - cell['center'][0], yy - cell['center'][1]
        angle, radius, stretch = cell['angle_rad'], cell['radius_mm'], cell['stretch']
        u, v = dx * math.cos(angle) + dy * math.sin(angle), -dx * math.sin(angle) + dy * math.cos(angle)
        strike = cell['depth_mm'] * np.maximum(0, 1 - (u / (radius * stretch)) ** 2 - (v / (radius / stretch)) ** 2)
        depression = np.maximum(depression, strike)
    # Reduce cut depth near the edge so the face always stays above the walls.
    depression *= np.clip(crown / 1.0, 0, 1)
    envelope = BASE_HEIGHT + crown
    return envelope, depression, envelope - depression


def make_mesh():
    """A single broad convex face with overlapping concave hammer impressions.

    The smooth crown provides the global bulge. Each local parabolic cut removes
    material from that envelope; individual texture features cannot protrude.
    """
    rng = np.random.default_rng(20261014)
    step = .2
    sites = []
    for _ in range(30000):
        candidate = np.round((rng.uniform(-10, 10, 2) + 12.5) / step) * step - 12.5
        if all(np.linalg.norm(candidate - other) >= 3.0 for other in sites):
            sites.append(candidate)
        if len(sites) == 30:
            break
    assert len(sites) == 30
    coords = np.linspace(-12.5, 12.5, 126)
    xx, yy = np.meshgrid(coords, coords)
    cells = []
    for i, site in enumerate(sites):
        depth = DIMPLE_DEPTH if i == 0 else float(rng.uniform(.48, .59))
        radius = float(rng.uniform(2.6, 3.2))
        stretch = float(rng.uniform(.88, 1.12))
        angle = float(rng.uniform(0, 2 * math.pi))
        cells.append(dict(center=site.tolist(), depth_mm=depth, radius_mm=radius, stretch=stretch, angle_rad=angle))
    envelope, depression, zz = surface_fields(xx, yy, cells)
    assert np.all(zz <= envelope + 1e-9) and np.all(zz >= BASE_HEIGHT - 1e-9)
    # Verify actual mesh samples at interior dimple centers curve UP in both
    # directions (a concave depression), even after the broad crown is applied.
    concavity_checks = []
    for cell in cells:
        i, j = [int(round((p + 12.5) / step)) for p in cell['center']]
        if envelope[j-1:j+2, i-1:i+2].min() >= BASE_HEIGHT + 1.0:
            x_curvature = (zz[j, i-1] - 2 * zz[j, i] + zz[j, i+1]) / step ** 2
            y_curvature = (zz[j-1, i] - 2 * zz[j, i] + zz[j+1, i]) / step ** 2
            assert x_curvature > 0 and y_curvature > 0, cell
            concavity_checks.append(dict(center=cell['center'], x_curvature=float(x_curvature), y_curvature=float(y_curvature)))
    assert len(concavity_checks) >= 10
    vertices = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()]).tolist()
    faces = []
    n = len(coords)
    for j in range(n - 1):
        for i in range(n - 1):
            a, b, c, d = j * n + i, j * n + i + 1, (j + 1) * n + i, (j + 1) * n + i + 1
            faces.extend([[a, b, d], [a, d, c]])
    boundary = (list(range(n)) + [j * n + n - 1 for j in range(1, n)]
                + [(n - 1) * n + i for i in range(n - 2, -1, -1)]
                + [j * n for j in range(n - 2, 0, -1)])
    bottom = []
    for index in boundary:
        bottom.append(len(vertices))
        vertices.append([*vertices[index][:2], 0])
    center = len(vertices)
    vertices.append([0, 0, 0])
    for j, index in enumerate(boundary):
        k = (j + 1) % len(boundary)
        faces.extend([[bottom[j], bottom[k], boundary[k]], [bottom[j], boundary[k], index],
                      [center, bottom[k], bottom[j]]])
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=True)
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.is_volume
    assert mesh.body_count == 1 and mesh.euler_number == 2
    max_height = float(zz.max())
    assert np.allclose(mesh.bounds, [[-12.5, -12.5, 0], [12.5, 12.5, max_height]])
    assert 1.3 < max_height - BASE_HEIGHT < CROWN_RISE
    top = mesh.face_normals[:, 2] > 1e-5
    assert abs(np.sum(mesh.area_faces[top] * mesh.face_normals[top, 2]) - 625) < 1e-5
    assert mesh.triangles[top, :, 2].min() >= BASE_HEIGHT - 1e-8
    max_slope = float(np.degrees(np.arccos(mesh.face_normals[top, 2])).max())
    assert max_slope < 60, max_slope
    areas = {str(z): float(mesh_slice(mesh, z).area) for z in [3.9, 4.1, 4.5, 4.9, 5.3]}
    assert abs(areas['3.9'] - 625) < 1e-5
    assert 625 > areas['4.1'] > areas['4.5'] > areas['4.9'] > areas['5.3'] > 0
    # Every higher cross-section must be supported by the section beneath it.
    sections = [mesh_slice(mesh, z) for z in np.arange(3.9, max_height, .2)]
    assert all(upper.difference(lower.buffer(1e-6)).area < 1e-5
               for lower, upper in zip(sections, sections[1:]))
    details = dict(dimensions_mm=[25, 25, max_height], border_width_mm=BORDER_WIDTH, minimum_thickness_mm=BASE_HEIGHT,
                   border_height_mm=BASE_HEIGHT, untextured_crown_rise_mm=CROWN_RISE,
                   actual_maximum_rise_above_walls_mm=max_height - BASE_HEIGHT,
                   maximum_dimple_depth_mm=float(depression.max()),
                   concave_dimple_center_checks=concavity_checks, maximum_protrusion_above_crown_mm=float((zz-envelope).max()),
                   cells=cells, grid_spacing_mm=step, maximum_face_slope_degrees=max_slope,
                   cross_section_area_mm2=areas, vertices=len(mesh.vertices), triangles=len(mesh.faces),
                   volume_mm3=float(mesh.volume), watertight=True, bodies=1, undercuts=False,
                   seed=20261014, construction='One broad domed face above 4 mm walls, with 30 overlapping concave parabolic dimples cut into its envelope')
    return mesh, details


def stage():
    WORK.mkdir(parents=True, exist_ok=True)
    assert not (WORK / 'manifest.json').exists(), 'Preserve existing test evidence; use a fresh work directory.'
    preserved = {name: sha(ROOT / name) for name in ['Dara.3mf',
        'working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf',
        'Dara-Copper-Diagnostic-Test.3mf', 'Dara-Copper-Thickness-Test.3mf']}
    source = read_zip(ROOT / 'Dara.3mf')
    settings = json.loads(source['Metadata/project_settings.config'])
    assert float(settings['layer_height']) == float(settings['initial_layer_print_height']) == .2
    assert settings['printer_model'] == 'Bambu Lab A1' and settings['nozzle_diameter'] == ['0.4']
    assert float(settings['filament_flow_ratio'][2]) == .96
    settings.update(print_settings_id=TITLE, print_sequence='by layer', enable_prime_tower='0', enable_support='0')
    mesh, geometry = make_mesh()
    mesh.export(WORK / 'coupon.stl')
    files = {'[Content_Types].xml': source['[Content_Types].xml'],
        '_rels/.rels': b'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>',
        'Metadata/project_settings.config': json.dumps(settings, indent=2).encode()}
    root = model()
    del root.attrib['xmlns:p']
    for key, value in [('Application', 'BambuStudio-02.08.02.61'), ('BambuStudio:3mfVersion', '1'),
                       ('Title', TITLE), ('Description', 'Single 25 x 25 mm copper coupon: one gently domed face above 4 mm walls, concave hammered dimples, and a verified 15% gyroid core.')]:
        ET.SubElement(root, tag('metadata'), name=key).text = value
    resources = ET.SubElement(root, tag('resources'))
    obj = ET.SubElement(resources, tag('object'), id='1000', type='model', attrib={'{' + P + '}UUID': uid()})
    path = '3D/Objects/Hammered-Coupon.model'
    ET.SubElement(ET.SubElement(obj, tag('components')), tag('component'), objectid='1001', transform=IDENTITY,
                  attrib={'{' + P + '}path': '/' + path, '{' + P + '}UUID': uid()})
    child = model()
    mesh_object(ET.SubElement(child, tag('resources')), 1001, mesh)
    files[path] = xml(child)
    build = ET.SubElement(root, tag('build'), attrib={'{' + P + '}UUID': uid()})
    ET.SubElement(build, tag('item'), objectid='1000', printable='1', transform='1 0 0 0 1 0 0 0 1 128 128 0',
                  attrib={'{' + P + '}UUID': uid()})
    relationships = ET.Element('Relationships', xmlns=R)
    ET.SubElement(relationships, 'Relationship', Target='/' + path, Id='rel-1',
                  Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
    config = ET.Element('config')
    obj = ET.SubElement(config, 'object', id='1000')
    for key, value in OVERRIDES.items():
        meta(obj, key, value)
    part = ET.SubElement(obj, 'part', id='1001', subtype='normal_part')
    meta(part, 'name', 'Domed face with concave hammered dimples and gyroid core')
    ET.SubElement(part, 'mesh_stat', face_count=str(len(mesh.faces)), edges_fixed='0', degenerate_facets='0',
                  facets_removed='0', facets_reversed='0', backwards_edges='0')
    plate = ET.SubElement(config, 'plate')
    for key, value in [('plater_id', 1), ('plater_name', TITLE), ('locked', 'false'),
                       ('filament_map_mode', 'Auto For Flush'), ('filament_maps', '1 1 1 1'), ('filament_volume_maps', '0 0 0 0')]:
        meta(plate, key, value)
    instance = ET.SubElement(plate, 'model_instance')
    for key, value in [('object_id', 1000), ('instance_id', 0), ('identify_id', 101)]:
        meta(instance, key, value)
    files.update({'3D/3dmodel.model': xml(root), '3D/_rels/3dmodel.model.rels': xml(relationships),
                  'Metadata/model_settings.config': xml(config)})
    write_zip(WORK / 'staged.3mf', files)
    (WORK / 'manifest.json').write_text(json.dumps(dict(preserved_hashes=preserved, geometry=geometry), indent=2))
    print(json.dumps(dict(staged=str(WORK / 'staged.3mf'), volume_mm3=geometry['volume_mm3'],
                         cells=len(geometry['cells']), section_areas=geometry['cross_section_area_mm2']), indent=2))


def slice_project():
    exe = Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    output = WORK / 'slice'
    output.mkdir(exist_ok=True)
    with (WORK / 'slice.log').open('w', encoding='utf-8') as log:
        result = subprocess.run([str(exe), '--slice', '1', '--export-3mf', 'sliced.3mf', '--outputdir', str(output),
                                 str(WORK / 'staged.3mf')], cwd=exe.parent, stdout=log, stderr=subprocess.STDOUT,
                                creationflags=subprocess.CREATE_NO_WINDOW)
    print(json.dumps(dict(return_code=result.returncode, log=str(WORK / 'slice.log'))))
    result.check_returncode()


def publish():
    manifest = json.loads((WORK / 'manifest.json').read_text())
    for path, digest in manifest['preserved_hashes'].items():
        assert sha(ROOT / path) == digest, f'Existing project changed: {path}'
    files = read_zip(WORK / 'slice/sliced.3mf')
    config = ET.fromstring(files['Metadata/model_settings.config'])
    assert len(config.findall('plate')) == len(config.findall('object')) == 1
    for key, value in OVERRIDES.items():
        actual = props(config.find('object'))[key]
        assert (float(actual) == float(value) if key == 'top_solid_infill_flow_ratio' else actual == value), (key, actual)
    settings = json.loads(files['Metadata/project_settings.config'])
    assert float(settings['filament_flow_ratio'][2]) == .96
    assert float(settings['layer_height']) == float(settings['initial_layer_print_height']) == .2
    assert settings['enable_support'] == settings['enable_prime_tower'] == '0'
    original, geometry = make_mesh()
    meshes = []
    for name, data in files.items():
        if name.startswith('3D/') and name.endswith('.model'):
            for item in ET.fromstring(data).iter(tag('mesh')):
                vertices = [[float(v.get(k)) for k in ['x', 'y', 'z']] for v in item.find(tag('vertices'))]
                faces = [[int(f.get(k)) for k in ['v1', 'v2', 'v3']] for f in item.find(tag('triangles'))]
                meshes.append(trimesh.Trimesh(vertices=vertices, faces=faces, process=True))
    assert len(meshes) == 1
    mesh = meshes[0]
    # Studio recenters local mesh coordinates and moves the build instance.
    # Compare geometry in the original coupon coordinates, including transforms.
    root = ET.fromstring(files['3D/3dmodel.model'])
    item = root.find(tag('build')).find(tag('item'))
    obj = root.find(tag('resources')).find(f"{tag('object')}[@id='{item.get('objectid')}']")
    component = obj.find(tag('components')).find(tag('component'))
    mesh.apply_transform(transform(item.get('transform')) @ transform(component.get('transform')))
    mesh.apply_translation([-128, -128, 0])
    assert mesh.is_volume and mesh.body_count == 1 and len(mesh.faces) == len(original.faces)
    assert nearest_error(original.vertices, mesh.vertices) < 1e-5 and nearest_error(mesh.vertices, original.vertices) < 1e-5
    assert abs(mesh.volume - original.volume) < .001
    info = ET.fromstring(files['Metadata/slice_info.config'])
    plate = info.find('plate')
    assert len(info.findall('plate')) == 1
    setmeta(plate, 'printer_model_id', 'N2S')
    repairs = []
    for entry in list(plate.findall('metadata')):
        if entry.get('key') == 'first_layer_time':
            value = float(entry.get('value'))
            if not math.isfinite(value) or not 0 <= value <= float(props(plate)['prediction']):
                repairs.append(dict(key='first_layer_time', value=entry.get('value'), action='omit invalid optional display metadata'))
                plate.remove(entry)
    files['Metadata/slice_info.config'] = xml(info)
    gcode = files['Metadata/plate_1.gcode'].decode()
    audit = scan_gcode(gcode)
    assert audit['conservative_bed_edge_clearance_mm'] > 100
    assert set(audit['model_extrusion_z_by_filament_mm']) == {'3'}
    assert not any('Support' in name or 'Ironing' in name for name in audit['features'])
    records, pauses = inspect_moves(gcode, [dict(label='H', xy=[128, 128])], (12.5, 12.5))
    assert not pauses
    moves = records['H']
    last_z = max(m['z'] for m in moves)
    assert abs(last_z - geometry['dimensions_mm'][2]) <= .20001
    assert sorted({m['z'] for m in moves}) == [round(i * .2, 1) for i in range(1, round(last_z / .2) + 1)]
    top = [m for m in moves if m['feature'] == 'Top surface']
    top_layers = sorted({m['z'] for m in top})
    # A narrow crest at the very top may be filled entirely by a perimeter.
    assert len(top_layers) >= 6 and min(top_layers) >= BASE_HEIGHT and max(top_layers) >= last_z - .20001
    assert top and max(m['speed'] for m in top) <= 30.001
    # Ensure the last texture layer includes internal contour paths, not only a border.
    last_interior = [m for m in moves if m['z'] == last_z and 'wall' in m['feature'].lower()
                     and max(abs(v - 128) for xy in [m['start'], m['end']] for v in xy) < 10.5]
    assert last_interior, 'The highest layer must belong to the crown, not the border.'
    sparse = [m for m in moves if m['feature'] == 'Sparse infill']
    sparse_layers = sorted({m['z'] for m in sparse})
    assert len(sparse_layers) >= 8, sparse_layers
    # Sparse moves must cross the central region, not just survive in edge slivers.
    center_sparse_layers = sorted({m['z'] for m in sparse
        if max(abs((a + b) / 2 - 128) for a, b in zip(m['start'], m['end'])) < 7.5})
    assert len(center_sparse_layers) >= 8, center_sparse_layers
    sparse_length = sum(m['length'] for m in sparse)
    assert sparse_length > 1000, sparse_length
    result = json.loads((WORK / 'slice/result.json').read_text())
    assert result['return_code'] == 0
    write_zip(TARGET, files)
    read_zip(TARGET)
    report = dict(project=TARGET.name, project_sha256=sha(TARGET), preserved_hashes=manifest['preserved_hashes'],
        geometry=geometry, filament_slot=3, base_filament_flow_ratio=.96, top_flow_multiplier=1,
        layer_height_mm=.2, top_surface_layers_mm=top_layers, interior_wall_moves_at_final_layer=len(last_interior),
        infill=dict(pattern='gyroid', density_percent=15, sparse_layers_mm=sparse_layers,
                    central_sparse_layers_mm=center_sparse_layers, total_sparse_path_length_mm=sparse_length),
        toolpath_audit=audit, slicer_result=result, slice_metadata_repairs=repairs,
        limitations=['Appearance sample only; the actual silk sheen and layer stepping require a physical print.',
                    'The AI concept is a style reference, not an exact prediction of this mesh or its printed surface.',
                    'The crown and dimples are approximated by 0.2 mm layers. Contour steps remain visible.',
                    'This sample contains a verified sparse gyroid core; its short paths and cooling still differ from the full M.'])
    REPORT.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    seconds, grams = int(props(plate)['prediction']), float(props(plate)['weight'])
    (ROOT / 'Dara-Copper-Hammered-Test.txt').write_text(f'''HAMMERED COPPER SAMPLE - ONE DOMED FACE WITH CONCAVE DIMPLES

Open Dara-Copper-Hammered-Test.3mf as a project in Bambu Studio.
One sliced plate for Bambu A1 / 0.4 mm nozzle / textured PEI.
Map project filament 3 to copper SUNLU Silk 2.0. Use normal 100% printer speed.

Single 25 x 25 mm coupon, 4.0 mm walls, {geometry['dimensions_mm'][2]:.2f} mm maximum mesh height.
The WHOLE FACE forms one gentle dome above the side walls. Thirty shallow,
overlapping concave hammer marks are cut DOWN into that curved face.
Dimples are approximately 4-6 mm across after overlap, up to 0.6 mm deep;
their depth fades near the edge so the face stays above the walls.
The nominal crown rises 2 mm before dimpling; the finished mesh rises
{geometry['actual_maximum_rise_above_walls_mm']:.2f} mm above the 0.5 mm smooth edge. Sliced height: {last_z:.1f} mm.
This replaces the incorrect individual-bump sample.
This is actual mesh relief, not fuzzy skin or an image pasted onto a flat face.
No supports, brim, inspection pause, or ironing.
Estimated {grams:.2f} g and {seconds // 60} min {seconds % 60} sec;
printer preparation/purge can add material.

Uses the selected copper C settings: 0.2 mm layers including the first,
0.96 base filament flow, 100% top multiplier, 30 mm/s top surface,
40 mm/s outer wall, 50 mm/s internal solid fill, eight top shell layers /
1.6 mm, 15% gyroid, 220 C nozzle and 55 C textured PEI bed.
The 15% gyroid was verified in the generated toolpaths, including the
center of the coupon on {len(center_sparse_layers)} layers, Z={center_sparse_layers[0]:.1f}
through {center_sparse_layers[-1]:.1f} mm. Four bottom layers / 0.8 mm and
eight top layers / 1.6 mm leave a sparse core inside the 4 mm base.
In Preview, lower the upper layer slider to about Z=2.0 mm to inspect it.
The crown and dimples use 0.2 mm layers. Rounded geometry will still
print with visible contour steps; this sample tests whether you like that finish.

Let it cool, then view it upright as the M will hang. Tilt it under the
same room lighting and compare the textured face with the smooth sides.
Judge whether the intentional texture masks the unwanted fine crosshatch,
whether the copper highlights remain attractive, and whether the scale is right.
The concept rendering is not a guarantee of the printed finish.
This separate sample does not change the M or any existing test project.
''', encoding='utf-8')
    (WORK / 'plate.png').write_bytes(files['Metadata/plate_1.png'])
    render_preview(mesh, geometry)
    print(json.dumps(dict(project=str(TARGET), weight_g=grams, seconds=seconds,
                         texture_layers_mm=top_layers, infill_layers_mm=sparse_layers,
                         preview=str(PREVIEW)), indent=2))


def render_preview(mesh, geometry):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(8, 8), facecolor='#f3f1ed')
    ax = fig.add_axes([0, .28, 1, .65], projection='3d')
    ax.set_facecolor('#f3f1ed')
    light = np.array([-.4, -.6, .7])
    light /= np.linalg.norm(light)
    elev, azim = math.radians(40), math.radians(-65)
    camera = np.array([math.cos(elev) * math.cos(azim), math.cos(elev) * math.sin(azim), math.sin(elev)])
    visible = mesh.face_normals @ camera > 0
    shade = .50 + .5 * np.maximum(mesh.face_normals[visible] @ light, 0)
    colors = np.array([.85, .46, .25])[None, :] * shade[:, None]
    ax.add_collection3d(Poly3DCollection(mesh.triangles[visible], facecolors=colors, edgecolors='none', antialiaseds=False))
    ax.set_xlim(-13, 13)
    ax.set_ylim(-13, 13)
    ax.set_zlim(0, BASE_HEIGHT + CROWN_RISE)
    ax.set_box_aspect([26, 26, BASE_HEIGHT + CROWN_RISE])
    ax.view_init(elev=40, azim=-65)
    ax.set_axis_off()
    fig.suptitle('One domed face with hammered dimples', fontsize=16, y=.96)
    # A true-scale section makes the global bulge and subtractive dimples clear.
    profile = fig.add_axes([.12, .115, .76, .20], facecolor='#f3f1ed')
    xs = np.linspace(-12.5, 12.5, 501)
    envelope, _, zs = surface_fields(xs, np.zeros_like(xs), geometry['cells'])
    profile.fill_between(xs, BASE_HEIGHT, zs, color='#b76b3b', alpha=.6)
    profile.plot(xs, envelope, '--', color='#777777', lw=1.2, label='Smooth dome before dimpling')
    profile.plot(xs, zs, color='#7d3418', lw=1.5, label='Actual dimpled face')
    profile.axhline(BASE_HEIGHT, color='#555555', lw=1)
    profile.text(-12.2, BASE_HEIGHT - .3, 'Wall height', fontsize=9, va='top')
    profile.set_xlim(-13, 13)
    profile.set_ylim(3.2, 6.5)
    profile.set_aspect('equal')
    profile.set_axis_off()
    profile.set_title('Cross-section through the center (true scale)', fontsize=10)
    profile.legend(loc='lower center', bbox_to_anchor=(.5, -.9), frameon=False, fontsize=8, ncol=2)
    fig.text(.5, .025, '25 x 25 mm | 4 mm walls with gyroid core | shallow concave dimples\nActual geometry; printed sheen and layer steps will differ.',
             ha='center', fontsize=10, color='#444444')
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(PREVIEW, dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['stage', 'slice', 'publish'])
    command = parser.parse_args().command
    {'stage': stage, 'slice': slice_project, 'publish': publish}[command]()
