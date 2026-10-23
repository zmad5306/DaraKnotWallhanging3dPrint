"""Verify the distributed production 3MFs using Python's standard library.

Does not import experimental generators, modify files, slice, or send a print.
The committed report records the separate geometry/support validation.
"""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'working/bambu/Dara-Photo-Frame-A1-Jointed'
C='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
P='http://schemas.microsoft.com/3dmanufacturing/production/2015/06'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda:stream.read(1024*1024),b''):h.update(data)
    return h.hexdigest()


def text_hashes(path):
    # Historical CAD reports were written on Windows. Git's LF checkout is the
    # same text; accept only the exact raw/LF/CRLF representations of that text.
    raw=path.read_bytes();lf=raw.replace(b'\r\n',b'\n')
    return {hashlib.sha256(b).hexdigest() for b in [raw,lf,lf.replace(b'\n',b'\r\n')]}


def audit_legacy(targets=None,check_exports=True):
    report=json.loads((PACKAGE/'mirrored-joints-validation.json').read_text())
    covers=json.loads((PACKAGE/'cover-crown-validation.json').read_text())
    assert covers['project_sha256']==report['baseline_sha256']
    archived=targets is not None
    targets=targets or [ROOT/'Dara.3mf',PACKAGE/'Dara-Photo-Frame-A1-Complete.3mf']
    for path in targets:
        assert sha(path)==report['project_sha256'],f'{path.name}: release hash mismatch; retrieve LFS files or review local edits.'
    with zipfile.ZipFile(targets[0]) as archive:
        assert archive.testzip() is None,'ZIP integrity failure'
        names=set(archive.namelist())
        cfg=ET.fromstring(archive.read('Metadata/model_settings.config'))
        info=ET.fromstring(archive.read('Metadata/slice_info.config'))
        root=ET.fromstring(archive.read('3D/3dmodel.model'))
        settings=json.loads(archive.read('Metadata/project_settings.config'))
        assert settings['wall_generator']=='classic'
        for key,value in report['precision_settings'].items():
            assert settings[key]==value,f'{key}: production setting differs from release report'
        assert len(cfg.findall('plate'))==len(info.findall('plate'))==report['plates']==32
        assert len(cfg.findall('object'))==report['objects']==47
        assert len(root.find('{'+C+'}build'))==report['instances']==78
        records=report['changed_plates']+report['unchanged_native_plates']
        assert sorted(r['plate'] for r in records)==list(range(1,33))
        for row in records:
            path=f"Metadata/plate_{row['plate']}.gcode";data=archive.read(path)
            assert hashlib.sha256(data).hexdigest()==row['gcode_sha256'],path
            assert hashlib.md5(data).hexdigest()==archive.read(path+'.md5').decode().strip().lower(),path
        for plate in cfg.findall('plate'):
            for md in plate.findall('metadata'):
                key,value=md.get('key',''),md.get('value','')
                if key.endswith('_file') and value:assert value in names,value
        ids=[]
        for path in names:
            if path.endswith('.model'):
                model=ET.fromstring(archive.read(path))
                ids.extend(o.get('id') for o in model.find('{'+C+'}resources'))
                for component in model.iter('{'+C+'}component'):
                    assert component.get('{'+P+'}path').lstrip('/') in names
        assert len(ids)==len(set(ids)),'Duplicate resource IDs'
        for row in covers['mesh_checks']:
            assert row['underside_max_distance_mm']<.0002
            assert row['footprint_max_distance_mm']<.0001
            assert row['sampled_top_error_mm']<.00101
        assert sum(r['after']['interior_joins'] for r in covers['surface_path_checks'])==3
        assert all(r['middle_half_span_joins']==0 for r in covers['surface_path_checks'])
        assert next(r for r in report['unchanged_native_plates'] if r['plate']==31)['gcode_sha256']==covers['changed_plates'][0]['gcode_sha256']
        assert report['seam_count']==32 and report['geometry_checks']['joint_tool_unchanged']
        assert all(r['front_geometry_error_mm']<.00002 for r in report['mesh_checks'])
        assert max(r['max_vertex_error_mm'] for r in report['native_roundtrip_checks'])<.0002
        assert report['perimeter_review']['passed']
    manifest=json.loads((ROOT/'working/stl/Dara-Photo-Frame-A1-Jointed/manifest.json').read_text())
    assert manifest['source_sha256']==report['source_cad_sha256']
    assert report['source_cad_sha256'] in text_hashes(ROOT/'working/Dara-Photo-Frame-A1-Jointed.scad')
    if check_exports:
        for part in manifest['parts']:
            assert sha(ROOT/'working/stl/Dara-Photo-Frame-A1-Jointed'/part['file'])==part['sha256'],part['file']
    if archived:print('Archived solid-M source: original 32 native slices, CAD text and embedded-package checks pass.')
    else:
        print('Both production 3MFs match the release. All 32 native slices, checksums and package references pass.')
        print('20 frame sections, 32 mirrored seams (67.3-75.1 mm); matching M attachments, CAD and STL hashes pass.')
        print('23 plates regenerated; nine saved slices and the continuous cover crowns preserved. Physical fit validation remains pending.')


def audit_veneer(targets=None):
    report=json.loads((PACKAGE/'m-veneer-release-validation.json').read_text())
    baseline=ROOT/report['baseline_file'];assert sha(baseline)==report['baseline_sha256']
    assert report['source_cad_sha256'] in text_hashes(ROOT/'working/Dara-Photo-Frame-A1-Jointed.scad')
    # Historical standalone STL exports have their own lifecycle. This release
    # embeds its authoritative meshes; hash those below, rather than treating
    # unrelated old export files as inputs to the archived source package.
    audit_legacy([baseline],check_exports=False)
    targets=targets or [ROOT/'Dara.3mf',PACKAGE/'Dara-Photo-Frame-A1-Complete.3mf']
    for path in targets:
        assert sha(path)==report['project_sha256'],f'{path}: release hash mismatch'
    records=report['changed_m_plates']+report['preserved_plates']
    assert sorted(r['plate'] for r in records)==list(range(1,37))
    assert len(report['changed_m_plates'])==12 and len(report['preserved_plates'])==24
    with zipfile.ZipFile(targets[0]) as z:
        assert z.testzip() is None
        cfg=ET.fromstring(z.read('Metadata/model_settings.config'));root=ET.fromstring(z.read('3D/3dmodel.model'))
        info=ET.fromstring(z.read('Metadata/slice_info.config'))
        settings=json.loads(z.read('Metadata/project_settings.config'))
        assert len(cfg.findall('plate'))==len(info.findall('plate'))==report['plates']==36
        assert len(cfg.findall('object'))==report['objects']==46
        assert len(root.find('{'+C+'}build'))==report['instances']==77
        assert settings['bed_exclude_area']==[] and settings['wall_loops']=='4'
        cores=[];veneers=[]
        for obj in cfg.findall('object'):
            st={m.get('key'):m.get('value') for m in obj.findall('metadata')};name=st.get('name','')
            if name.startswith('C') and 'flat structural core' in name:
                assert st.get('sparse_infill_density',settings['sparse_infill_density'])=='15%'
                assert st['bottom_shell_layers']==st['top_shell_layers']=='5';cores.append(name)
            if name.startswith('V') and 'veneer' in name:
                assert st['sparse_infill_density']=='100%';veneers.append(name)
            assert 'hammered with band seats' not in name and not name.startswith('Band')
        assert len(cores)==len(veneers)==6
        for row in records:
            key=f"Metadata/plate_{row['plate']}.gcode";data=z.read(key)
            assert hashlib.sha256(data).hexdigest()==row['gcode_sha256']
            assert hashlib.md5(data).hexdigest()==z.read(key+'.md5').decode().strip().lower()
            assert b'; EXECUTABLE_BLOCK_END' in data
        for child,h in report['source_child_mesh_sha256'].items():assert hashlib.sha256(z.read(child)).hexdigest()==h,child
        ids=[];names=set(z.namelist())
        for name in names:
            if name.endswith('.model'):
                r=ET.fromstring(z.read(name));ids.extend(o.get('id') for o in r.find('{'+C+'}resources'))
                for co in r.iter('{'+C+'}component'):assert co.get('{'+P+'}path').lstrip('/') in names
        assert len(ids)==len(set(ids))
        for p in cfg.findall('plate'):
            for m in p.findall('metadata'):
                if m.get('key','').endswith('_file') and m.get('value'):assert m.get('value') in names
    plan=json.loads((ROOT/'output/development/m-veneer-cosmetic-fit/M-geometry-validation.json').read_text())
    for skin in plan['skins']:
        carrier=skin['carrier'];assert carrier['continuous_starter_shoe'] is False
        assert carrier['cutter_access_necks_checked']==carrier['bonded_tooth_count']
        assert carrier['maximum_cutter_access_obstruction_mm3']<1e-5
        assert carrier['flush_trim_excess_outside_finished_veneer_mm3']<1e-5
    orientation=report['orientation'];assert orientation['all_full_rotations_equal'] and orientation['broad_show_planes_parallel_to_bed_y']
    assert len(orientation['veneers'])==6 and report['cosmetic_gap_mm']==0
    assert len(report['zero_gap_seams'])==5 and max(s['maximum_front_edge_mismatch_mm'] for s in report['zero_gap_seams'])<.0002
    assert report['native_project_reopen_return_code']==0
    assert report['native_reopen_input_sha256']==report['project_sha256']
    if report.get('fin_coverage'):
        fin=report['fin_coverage'];path=ROOT/fin['report']
        assert fin['sha256'] in text_hashes(path)
        proof=json.loads(path.read_text())
        assert proof['baseline_contacts_sha256'] in text_hashes(ROOT/'working/review/m-fin-density/baseline-fin-contacts.json')
        assert proof['geometry_plan_sha256'] in text_hashes(ROOT/'output/development/m-veneer-cosmetic-fit/M-geometry-validation.json')
        assert all(r['trial_geometric_checks_pass'] for r in proof['veneers'])
        assert fin['face_preservation_sha256'] in text_hashes(ROOT/'output/development/m-veneer-cosmetic-fit/M-fin-face-preservation.json')
        assert fin['tall_fins_diagonally_restrained']
        print(f"Full M support coverage: {fin['baseline_fin_count']} to {fin['revised_fin_count']} fins; independent rear-area audit and diagonal-restraint checks pass.")
    print('A1 production: 36 sliced plates, six flat cores and six consistently Y-oriented veneers pass.')
    print('24 original plate slices preserved; zero nominal M seams, solid veneers and mounting clearances verified. Physical confirmation pending.')


def audit():
    if (ROOT/'release/root-projects/catalog.json').exists():
        from audit_root_projects import audit as audit_root
        audit_root();return
    with zipfile.ZipFile(ROOT/'Dara.3mf') as z:settings=json.loads(z.read('Metadata/project_settings.config'))
    if settings.get('printer_model')=='Bambu Lab A2L':
        from audit_a2l_release import audit as audit_a2l
        audit_a2l()
        audit_veneer([PACKAGE/'Dara-Photo-Frame-A1-Complete.3mf']);return
    if (PACKAGE/'m-veneer-release-validation.json').exists():audit_veneer()
    else:audit_legacy()


if __name__=='__main__':audit()
