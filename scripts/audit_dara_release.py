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


def audit():
    report=json.loads((PACKAGE/'cover-crown-validation.json').read_text())
    targets=[ROOT/'Dara.3mf',PACKAGE/'Dara-Photo-Frame-A1-Complete.3mf']
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
        for row in report['mesh_checks']:
            assert row['underside_max_distance_mm']<.0002
            assert row['footprint_max_distance_mm']<.0001
            assert row['sampled_top_error_mm']<.00101
        assert sum(r['after']['interior_joins'] for r in report['surface_path_checks'])==3
        assert all(r['middle_half_span_joins']==0 for r in report['surface_path_checks'])
    print('Both production 3MFs match the release. All 32 native slices, checksums and package references pass.')
    print('Five rebuilt cover crowns: repeated middle-face junction tracks removed; three isolated end transitions remain.')
    print('Resolution is now 0.05 mm globally; the other 31 saved slices are preserved. Physical print validation remains pending.')


if __name__=='__main__':audit()
