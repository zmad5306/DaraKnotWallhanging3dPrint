"""Separate diagnostic prints cropped from the production V2 mesh.

No production project is modified. These are physical checks, not a substitute
for qualifying a full-width production part under its actual moving mass.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'.work/python-libs'))
import numpy as np
import manifold3d as mf
from development_3mf import solid, mesh, write_project, save_json, sha
from validate_production_split import Project, distance
from validate_print_project import scan_gcode
from build_a2l_flush_joint_test import protected

OUT = ROOT/'working/bambu/Dara-A2L-Veneer-Print-Checks'
WORK = ROOT/'.work/veneer-print-checks'
SOURCE = ROOT/'working/bambu/Dara-Photo-Frame-A2L/Dara-A2L-Editable.3mf'
SPECS = {
    '01-Start-12mm': dict(lo=[0,0,0], hi=[330,320,12],
        purpose='Production plate 16, complete footprint and first 12 mm. Tests bed adhesion, starter edges and localized tree contacts.',
        limitation='Cut creates a new top surface. Does not test higher local starts, tall stability or full print duration.'),
    '02-Tall-Fin-Witness': dict(lo=[50,197,0], hi=[100,225,325],
        purpose='Production plate 16, two original fin rows 23.5165 mm apart and their veneer, braces and contacts, to 297.1 mm.',
        limitation='Cropped neighbors and much lower mass change stiffness, cooling and dynamics. Passing does not qualify a full-width production veneer.'),
}


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    fingerprints = protected()
    source = Project(SOURCE)
    native = Project(ROOT/'Dara.3mf')
    row = source.rows['V2 A2L hammered veneer and sacrificial fins']
    assert len(row['parts']) == 1
    body = solid(row['parts'][0]['mesh']).transform(row['T'][:3])
    plan = json.loads((SOURCE.parent/'production-plan.json').read_text())
    front = np.asarray(plan['veneer_rotation'])[:,2]
    records = {}
    for name,spec in SPECS.items():
        lo,hi=np.asarray(spec['lo']),np.asarray(spec['hi'])
        clipped = body ^ mf.Manifold.cube(hi-lo).translate(lo)
        components = [q for q in clipped.decompose() if q.volume()>1e-6]
        assert len(components)==1, (name,len(components))
        m=mesh(clipped)
        assert m.is_volume and abs(m.bounds[0,2])<1e-6
        assert (clipped-body).volume()<1e-7
        settings=dict(native.settings,wipe_tower_x=['285'],wipe_tower_y=['160'])
        title='A2L veneer diagnostic - '+name
        settings['print_settings_id']=title
        entry=dict(name=name,parts=[dict(mesh=m,settings=row['parts'][0]['settings'])],
            transform=np.eye(4),settings=row['settings'],block_front=True,front_normal=front)
        path=OUT/(name+'-Editable.3mf')
        write_project(path,[[entry]],title,settings_update=settings)
        sidecar=json.loads(path.with_suffix('.json').read_text())
        sidecar.update(source_project=str(SOURCE.relative_to(ROOT)),source_sha256=sha(SOURCE),source_plate=16)
        save_json(path.with_suffix('.json'),sidecar)
        records[name]=dict(**spec,bounds_mm=m.bounds.tolist(),volume_mm3=clipped.volume(),
            exact_crop_of_production=True,connected_components=1,added_geometry=False,
            editable_sha256=sha(path),settings_source_sha256=sha(ROOT/'Dara.3mf'))
    assert protected()==fingerprints
    save_json(OUT/'geometry-validation.json',dict(status='DIGITAL_GEOMETRY_PASS_PHYSICAL_CHECKS_PENDING',
        source_sha256=sha(SOURCE),protected_project_sha256=fingerprints,tests=records))
    print(json.dumps(records,indent=2),flush=True)


def slice_all():
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    for name in SPECS:
        folder=WORK/name
        folder.mkdir(parents=True,exist_ok=True)
        with (folder/'cli.log').open('w') as log:
            result=subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf',
                '--outputdir',str(folder),str(OUT/(name+'-Editable.3mf'))],cwd=exe.parent,
                stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        result.check_returncode()
        print('Sliced '+name,flush=True)


def validate():
    report=json.loads((OUT/'geometry-validation.json').read_text())
    results={}
    for name in SPECS:
        source=Project(OUT/(name+'-Editable.3mf'))
        native=Project(WORK/name/'sliced.3mf')
        assert source.rows.keys()==native.rows.keys()
        assert source.settings==native.settings
        errors=[]
        for key,after in native.rows.items():
            before=source.rows[key]
            assert after['settings']['enable_support']=='1'
            assert after['settings']['extruder']=='3'
            assert len(after['parts'])==len(before['parts'])==1
            a,b=after['parts'][0]['mesh'],before['parts'][0]['mesh']
            assert a.is_volume
            av=a.vertices@after['T'][:3,:3].T+after['T'][:3,3]
            bv=b.vertices@before['T'][:3,:3].T+before['T'][:3,3]
            errors.append(distance(av,bv))
            assert errors[-1]<.001
        raw=native.z.read('Metadata/plate_1.gcode')
        assert hashlib.md5(raw).hexdigest()==native.z.read('Metadata/plate_1.gcode.md5').decode().strip().lower()
        gcode=raw.decode()
        scan=scan_gcode(gcode)
        lo,hi=np.array(scan['bead_xy_bounds_mm'])
        margin=float(min(*lo,*(np.array([330,320])-hi)))
        assert margin>.5
        scan['conservative_bed_edge_clearance_mm']=margin
        assert set(scan['model_extrusion_z_by_filament_mm'])=={'3'}
        assert max(scan['model_extrusion_z_by_filament_mm']['3'])<325
        info=ET.fromstring(native.z.read('Metadata/slice_info.config'))
        warnings=[w.attrib for p in info.findall('plate') for w in p.findall('warning')]
        assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings),warnings
        estimate=json.loads((WORK/name/'result.json').read_text())
        result=dict(maximum_native_mesh_pose_error_mm=max(errors),scan=scan,
            slicer_warnings=warnings,native_result=estimate,gcode_sha256=hashlib.sha256(raw).hexdigest())
        final=OUT/(name+'.3mf')
        final.write_bytes((WORK/name/'sliced.3mf').read_bytes())
        result['project_sha256']=sha(final)
        results[name]=result
        sidecar=json.loads((OUT/(name+'-Editable.json')).read_text())
        sidecar.update(native_slice_validated=True,native_project=final.name,native_sha256=sha(final),physical_confirmation_pending=True)
        save_json(OUT/(name+'-Editable.json'),sidecar)
    assert protected()==report['protected_project_sha256']
    save_json(OUT/'native-validation.json',dict(status='DIGITAL_PASS_PHYSICAL_CHECKS_PENDING',
        production_and_A1_preserved=True,tests=results,builder_sha256=sha(Path(__file__))))
    print('Both separate diagnostic projects passed native checks. Production unchanged.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('action',choices=['build','slice','validate'])
    {'build':build,'slice':slice_all,'validate':validate}[p.parse_args().action]()
