"""Factorial, slicer-only comparison of fin access and support threshold.

The no-fin cases are deliberately not printable candidates: they isolate tree
generation after removing the carrier above the existing 1.6 mm base level.
All production packages remain unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.work/python-libs'))
import numpy as np
import manifold3d as mf
import shapely
from development_3mf import solid,mesh,write_project,save_json,sha
from validate_production_split import Project,distance
from build_a2l_flush_joint_test import protected
from check_veneer_layer_overlap import parse,coverage

OUT=ROOT/'working/review/veneer-support-comparison'
WORK=ROOT/'.work/veneer-support-comparison'
SOURCE=ROOT/'working/bambu/Dara-Photo-Frame-A2L/Dara-A2L-Editable.3mf'
CASES=['fins-30','fins-60','no-fins-30','no-fins-60']


def build():
    OUT.mkdir(parents=True,exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)
    fingerprints=protected()
    p=Project(SOURCE);native=Project(ROOT/'Dara.3mf')
    row=p.rows['V2 A2L hammered veneer and sacrificial fins']
    body=solid(row['parts'][0]['mesh']).transform(row['T'][:3])
    geometry=json.loads((SOURCE.parent/'M-geometry-validation.json').read_text())
    pose=np.array(geometry['skins'][1]['assembly_to_printer'])
    rear=mf.Manifold.cube([2000,2000,40]).translate([-1000,-1000,8.6]).transform(pose[:3])
    base=mf.Manifold.cube([330,320,1.6])
    no_fins=(body^rear)+(body^base)
    assert (no_fins-body).volume()<1e-7
    records={}
    for name in CASES:
        folder=WORK/name;folder.mkdir(parents=True,exist_ok=True)
        threshold=name.rsplit('-',1)[1]
        b=no_fins if name.startswith('no-fins') else body
        st=dict(row['settings'],support_threshold_angle=threshold)
        settings=dict(native.settings,print_settings_id='DO NOT PRINT - support comparison '+name,
            wipe_tower_x=['285'],wipe_tower_y=['160'])
        entry=dict(name='DO NOT PRINT - '+name,parts=[dict(mesh=mesh(b),settings=row['parts'][0]['settings'])],
            settings=st,transform=np.eye(4),block_front=True,front_normal=pose[:3,2])
        write_project(folder/'input.3mf',[[entry]],settings['print_settings_id'],settings_update=settings)
        records[name]=dict(threshold_degrees=int(threshold),fins_present=not name.startswith('no-fins'),
            volume_mm3=b.volume(),bounds_mm=list(b.bounding_box()),input_sha256=sha(folder/'input.3mf'))
    assert protected()==fingerprints
    save_json(OUT/'inputs.json',dict(purpose='Slicer comparison only; no experiment is a production release.',
        protected_project_sha256=fingerprints,source_sha256=sha(SOURCE),cases=records,
        no_fins_method='Keep exact model at/above assembly back plane 8.6 mm and original base at print Z0-1.6; remove carrier between. Pose unchanged.'))
    print('Built four isolated support comparisons.',flush=True)


def slice_all():
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    for name in CASES:
        folder=WORK/name
        with (folder/'cli.log').open('w') as log:
            result=subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf',
                '--outputdir',str(folder),str(folder/'input.3mf')],cwd=exe.parent,
                stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        result.check_returncode()
        print('Sliced '+name,flush=True)


def analyze():
    inputs=json.loads((OUT/'inputs.json').read_text())
    geometry=json.loads((SOURCE.parent/'M-geometry-validation.json').read_text())
    pose=np.array(geometry['skins'][1]['assembly_to_printer'])
    p=Project(SOURCE)
    row=p.rows['V2 A2L hammered veneer and sacrificial fins']
    m=row['parts'][0]['mesh'].copy();m.apply_transform(row['T'])
    # Exact planar rear lands, excluding recessed openings and carrier sheets.
    av=(m.vertices-pose[:3,3])@pose[:3,:3]
    select=((m.face_normals@(-pose[:3,2]))>.99999)&np.all(np.abs(av[m.faces,2]-8.6)<1e-4,axis=1)
    lands=shapely.union_all(shapely.polygons(av[m.faces[select],:2]))
    xmin,ymin,xmax,ymax=lands.bounds
    xx,yy=np.meshgrid(np.arange(xmin+.371,xmax,1),np.arange(ymin+.619,ymax,1))
    xy=np.column_stack([xx.ravel(),yy.ravel()])
    xy=xy[shapely.contains_xy(lands,xy[:,0],xy[:,1])]
    xyz=np.column_stack([xy,np.full(len(xy),8.6)])@pose[:3,:3].T+pose[:3,3]
    bins=np.ceil(xyz[:,2]/.2).astype(int)
    results={};plots=[]
    for name in CASES:
        folder=WORK/name
        source=Project(folder/'input.3mf');native=Project(folder/'sliced.3mf')
        assert source.rows.keys()==native.rows.keys()
        before=next(iter(source.rows.values()));after=next(iter(native.rows.values()))
        av=before['parts'][0]['mesh'].vertices@before['T'][:3,:3].T+before['T'][:3,3]
        bv=after['parts'][0]['mesh'].vertices@after['T'][:3,:3].T+after['T'][:3,3]
        error=distance(av,bv);assert error<.001
        assert after['settings']['support_threshold_angle']==name.rsplit('-',1)[1]
        assert after['settings']['enable_support']=='1'
        assert native.settings==source.settings
        raw=native.z.read('Metadata/plate_1.gcode')
        assert hashlib.md5(raw).hexdigest()==native.z.read('Metadata/plate_1.gcode.md5').decode().strip().lower()
        model,support=parse(raw.decode())
        supported=np.zeros(len(xy),dtype=bool)
        for band in np.unique(bins):
            ids=np.flatnonzero(bins==band)
            for k in range(-4,1):
                z=round((band+k)*.2,4)
                rows=support.get(z,[])
                if not rows:continue
                gap=xyz[ids,2]-z
                valid=ids[(gap>=.05)&(gap<=.6001)]
                if len(valid):supported[valid]|=coverage(xyz[valid,:2],np.zeros(len(valid)),rows)[0]
        length=sum(float(np.hypot(r[2]-r[0],r[3]-r[1])) for rows in support.values() for r in rows)
        estimate=json.loads((folder/'result.json').read_text())['sliced_plates'][0]
        warnings=[w.attrib for pl in ET.fromstring(native.z.read('Metadata/slice_info.config')).findall('plate') for w in pl.findall('warning')]
        result=dict(maximum_mesh_pose_error_mm=error,support_layers=len(support),
            support_extrusion_length_mm=length,support_max_z_mm=max(support,default=0),
            rear_land_samples=len(xy),samples_with_nearby_support=int(supported.sum()),
            sampled_rear_land_support_proximity_percent=100*float(supported.mean()),
            estimated_hours=estimate['total_predication']/3600,
            estimated_total_filament_g=sum(f['total_used_g'] for f in estimate['filaments']),
            slicer_warnings=warnings,gcode_sha256=hashlib.sha256(raw).hexdigest(),
            native_sha256=sha(folder/'sliced.3mf'))
        results[name]=result;plots.append((name,supported))
        print(name,json.dumps(result),flush=True)
    # Include the actual saved production plate as an independent baseline.
    with zipfile.ZipFile(ROOT/'Dara.3mf') as z:raw=z.read('Metadata/plate_16.gcode')
    _,support=parse(raw.decode())
    baseline=dict(support_layers=len(support),support_max_z_mm=max(support),
        support_extrusion_length_mm=sum(float(np.hypot(r[2]-r[0],r[3]-r[1])) for rows in support.values() for r in rows),
        gcode_sha256=hashlib.sha256(raw).hexdigest())
    assert protected()==inputs['protected_project_sha256']
    save_json(OUT/'results.json',dict(status='SLICER_COMPARISON_ONLY_NOT_PHYSICALLY_QUALIFIED',
        method='One point per 1 mm grid square on exact planar rear lands. Nearby support means nominal support bead footprint under that XY point, 0.05 to 0.60 mm below it in printer Z. This is a coarse proximity screen, not continuous interface coverage or physical support effectiveness.',
        production_and_A1_preserved=True,cases=results,saved_production_baseline=baseline))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(12,9),layout='constrained')
    for ax,(name,mask) in zip(axes.ravel(),plots):
        ax.scatter(xy[~mask,0],xy[~mask,1],s=2,c='#d9d9d9',marker='s',linewidths=0)
        ax.scatter(xy[mask,0],xy[mask,1],s=3,c='#1a9165',marker='s',linewidths=0)
        result=results[name]
        ax.set_title(f"{name}: {result['sampled_rear_land_support_proximity_percent']:.1f}% sampled proximity")
        ax.set_aspect('equal');ax.set_xlabel('Assembly X (mm)');ax.set_ylabel('Assembly Y (mm)')
    fig.suptitle('Plate 16 rear lands: green = nearby printed tree path; gray = none\nSame pose and support settings except fin removal and 30° / 60° threshold',fontsize=13)
    fig.savefig(OUT/'rear-support-comparison.png',dpi=150)
    plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','slice','analyze'])
    {'build':build,'slice':slice_all,'analyze':analyze}[p.parse_args().action]()
