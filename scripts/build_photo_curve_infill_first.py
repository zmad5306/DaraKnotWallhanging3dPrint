# Historical design source retained for provenance, not a current rebuild command.
# Uses retired project paths/settings; do not regenerate current releases with it.
"""r3: exact r2 right-hand full curve, change print order to infill first."""
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.work/python-libs'))
import numpy as np
import shapely
from development_3mf import sha,save_json,props,tag
from extract_production_joint_sample import protected
from validate_production_split import Project,distance
from validate_print_project import scan_gcode
from build_photo_support_test import LOCKS,effective,paths

OLD=ROOT/'output/Dara-A2L-Photo-Curve-Support-Test-r2'
SOURCE=OLD/'Dara-A2L-Photo-Curve-Support-Test-r2-Editable.3mf'
NAME='Dara-A2L-Photo-Curve-Infill-First-r3'
OUT=ROOT/'output'/NAME
WORK=ROOT/'.work/photo-curve-infill-first-r3'
EDIT=OUT/(NAME+'-Editable.3mf')
FINAL=OUT/(NAME+'.3mf')
OBJECT='Full photo curve - 0.2 mm interface - INFILL FIRST r3'
TITLE='A2L full photo curve - 8% gyroid - infill first r3'
PRODUCTION=ROOT/'Dara.3mf'


def feature_order(text):
    z=0;obj=None;out=[]
    for number,line in enumerate(text.splitlines(),1):
        if line.startswith('; Z_HEIGHT:'):z=float(line.split(':',1)[1])
        if line.startswith('; start printing object'):obj=line.rsplit(': ',1)[1]
        if line.startswith('; stop printing object'):obj=None
        if z==2.6 and line.startswith('; FEATURE:'):
            out.append(dict(line=number,object=obj,feature=line.split(': ',1)[1]))
    return out


def run():
    OUT.mkdir(parents=True,exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)
    before=protected();prior=json.loads((OLD/'validation.json').read_text())
    assert sha(PRODUCTION)==prior['source_sha256'] and sha(SOURCE)==prior['editable_sha256']
    old=Project(SOURCE);source_name='RIGHT B - full curve - 0.2 mm interface'
    kept=old.rows[source_name]
    with zipfile.ZipFile(SOURCE) as z:files={n:z.read(n) for n in z.namelist()}
    cfg=ET.fromstring(files['Metadata/model_settings.config']);root=ET.fromstring(files['3D/3dmodel.model'])
    oid=next(o.get('id') for o in cfg.findall('object') if props(o).get('name')==source_name)
    other_ids=[o.get('id') for o in cfg.findall('object') if o.get('id')!=oid]
    for obj in list(cfg.findall('object')):
        if obj.get('id')!=oid:cfg.remove(obj)
        else:obj.find("metadata[@key='name']").set('value',OBJECT)
    plate=cfg.find('plate');plate.find("metadata[@key='plater_name']").set('value','1 - '+OBJECT)
    for inst in list(plate.findall('model_instance')):
        if props(inst)['object_id']!=oid:plate.remove(inst)
    resources=root.find(tag('resources'));build=root.find(tag('build'))
    for obj in list(resources):
        if obj.get('id') in other_ids:resources.remove(obj)
    for item in list(build):
        if item.get('objectid') in other_ids:build.remove(item)
    for md in root.findall(tag('metadata')):
        if md.get('name')=='Title':md.text=TITLE
    removed=[]
    for other in other_ids:
        asset=f'3D/Objects/{other}.model'
        if asset in files:removed.append('/'+asset);del files[asset]
    rels=ET.fromstring(files['3D/_rels/3dmodel.model.rels'])
    for rel in list(rels):
        if rel.get('Target') in removed:rels.remove(rel)
    # Bambu's native relationship reader expects the default namespace.
    clean_rels=ET.Element('Relationships',xmlns='http://schemas.openxmlformats.org/package/2006/relationships')
    for rel in rels:ET.SubElement(clean_rels,'Relationship',rel.attrib)
    rels=clean_rels
    settings=json.loads(files['Metadata/project_settings.config']);original_settings=settings.copy()
    assert settings['is_infill_first']=='0'
    settings['is_infill_first']='1';settings['print_settings_id']=TITLE
    files['Metadata/project_settings.config']=json.dumps(settings,indent=2).encode()
    for key,xml in [('Metadata/model_settings.config',cfg),('3D/3dmodel.model',root),('3D/_rels/3dmodel.model.rels',rels)]:
        files[key]=ET.tostring(xml,encoding='utf-8',xml_declaration=True)
    with zipfile.ZipFile(EDIT,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in files.items():z.writestr(n,b)
    (OUT/'crop-boundary.geojson').write_bytes((OLD/'crop-boundary.geojson').read_bytes())
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe');native=WORK/'native';native.mkdir(exist_ok=True)
    with (WORK/'slice.log').open('w',encoding='utf-8') as log:
        proc=subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf','--outputdir',str(native),str(EDIT)],
            cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    proc.check_returncode()
    edited=Project(EDIT);sliced=Project(native/'sliced.3mf');assert edited.settings==sliced.settings==settings
    assert len(edited.rows)==len(sliced.rows)==1
    differences={k:dict(before=original_settings.get(k),after=settings.get(k)) for k in set(settings)|set(original_settings) if original_settings.get(k)!=settings.get(k)}
    assert set(differences)=={'is_infill_first','print_settings_id'}
    geometry=[]
    for row in [edited.rows[OBJECT],sliced.rows[OBJECT]]:
        assert effective(row['settings'])==effective(kept['settings'])
        assert np.allclose(row['T'],kept['T'],atol=1e-8)
        assert len(row['parts'])==len(kept['parts'])
        for a,b in zip(row['parts'],kept['parts']):
            assert a['subtype']==b['subtype'] and a['mesh'].is_volume
            assert effective(a['settings'])==effective(b['settings'])
            err=distance(a['mesh'].vertices,b['mesh'].vertices);geometry.append(err);assert err<.001
            e={**settings,**effective(row['settings']),**effective(a['settings'])}
            for k,value in LOCKS.items():
                if k=='sparse_infill_density' and b['settings'].get(k)=='100%':value='100%'
                assert e[k]==value
            assert e['support_interface_spacing']=='0.2' and e['support_top_z_distance']=='0.2'
            assert e['is_infill_first']=='1'
    raw=sliced.z.read('Metadata/plate_1.gcode');g=raw.decode()
    assert hashlib.md5(raw).hexdigest()==sliced.z.read('Metadata/plate_1.gcode.md5').decode().strip().lower()
    gc={line[2:].split(' = ',1)[0]:line[2:].split(' = ',1)[1] for line in g.splitlines() if line.startswith('; ') and ' = ' in line}
    for k,v in LOCKS.items():assert gc[k]==v,(k,gc.get(k),v)
    assert gc['is_infill_first']=='1' and gc['printer_model']=='Bambu Lab A2L' and gc['nozzle_diameter']=='0.4'
    scan=scan_gcode(g);lo,hi=np.array(scan['bead_xy_bounds_mm']);scan['conservative_bed_edge_clearance_mm']=float(min(*lo,*(np.array([330,320])-hi)))
    assert scan['conservative_bed_edge_clearance_mm']>.5
    assert set(scan['model_extrusion_z_by_filament_mm'])=={'1'} and max(scan['model_extrusion_z_by_filament_mm']['1'])==4
    assert scan['features'].get('Prime tower',0)==0
    ps=paths(g);layer=[p for p in ps if p['z']==2.6]
    first=next(i for i,p in enumerate(layer) if p['feature']=='Overhang wall')
    end=next(i for i in range(first+1,len(layer)) if layer[i]['feature']!='Overhang wall')
    chain=layer[first:end]
    earlier=[p for p in layer[:first] if p['feature'] in ['Bridge','Gap infill','Internal solid infill']]
    assert len(earlier)>100
    fill=shapely.union_all([shapely.LineString(p['segment']).buffer(p['width']/2) for p in earlier])
    wall=shapely.union_all([shapely.LineString(p['segment']) for p in chain])
    samples=[]
    for line in getattr(wall,'geoms',[wall]):
        samples.extend(line.interpolate(d) for d in np.linspace(0,line.length,max(2,math.ceil(line.length/.2))))
    gaps=shapely.distance(samples,fill)
    order=feature_order(g);assert next(i for i,q in enumerate(order) if q['feature']=='Bridge')<next(i for i,q in enumerate(order) if q['feature']=='Overhang wall')
    roof=[p for p in ps if p['feature']=='Support interface' and p['z']==2.2]
    assert roof
    speeds={feature:sorted({p['speed'] for p in layer if p['feature']==feature}) for feature in ['Bridge','Overhang wall']}
    assert speeds=={'Bridge':[50.0],'Overhang wall':[10.0]},speeds
    info=ET.fromstring(sliced.z.read('Metadata/slice_info.config'));warnings=[w.attrib for p in info.findall('plate') for w in p.findall('warning')]
    assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings),warnings
    result=json.loads((native/'result.json').read_text());assert result['return_code']==0
    estimate=result['sliced_plates'][0];assert protected()==before
    FINAL.write_bytes((native/'sliced.3mf').read_bytes())
    for n in ['plate_1.png','top_1.png']:(OUT/('saved-'+n)).write_bytes(sliced.z.read('Metadata/'+n))
    contact=dict(first_curved_wall_chain_length_mm=wall.length,fill_segments_already_printed=len(earlier),
        median_distance_to_prior_fill_beads_mm=float(np.median(gaps)),max_distance_to_prior_fill_beads_mm=float(gaps.max()),
        wall_centerline_probes_within_0_225mm_of_prior_fill_percent=float(np.mean(gaps<=.225)*100),
        caveat='Geometric bead proximity does not establish physical bonding.')
    report=dict(status='DIGITAL_CHECKS_PASSED_INFILL_FIRST_PHYSICAL_RESULT_PENDING',revision='r3',
        current_file=str(FINAL),current_sha256=sha(FINAL),editable_sha256=sha(EDIT),
        source_production=str(PRODUCTION),source_production_sha256=sha(PRODUCTION),
        source_r2_editable=str(SOURCE),source_r2_editable_sha256=sha(SOURCE),source_r2_print_sha256=prior['current_sha256'],
        source_object=source_name,source_crop_definition=prior['source_crop_definition'],
        crop_boundary_sha256=sha(OUT/'crop-boundary.geojson'),source_production_object='F2 A2L knot / plate 2 / object 22',
        source_source_volume_crops=prior['source_volume_crops'],retained_source_bounds_mm=prior['retained_source_bounds_mm'],
        coupon_size_mm=prior['coupon_size_mm'],translation_from_production_plate_mm=prior['translation_only_mm'][1],
        design_changes='None. Exact retained r2 right-hand geometry, settings, rotation and bed placement.',
        changed_variable='Print infill first: is_infill_first 0 -> 1; model fill before walls.',
        other_packaging_changes='Remove the other test object; descriptive test/object names updated.',
        global_settings_changes_from_r2=differences,all_effective_volume_object_settings_preserved=True,
        max_native_mesh_error_mm=max(geometry),locked_settings_checked_in_editable_sliced_and_gcode=True,
        gcode_md5_verified=True,gcode_sha256=hashlib.sha256(raw).hexdigest(),scan=scan,
        z2_6_feature_sequence=order,prior_fill_contact=contact,z2_6_speeds_mm_s=speeds,
        roof_top_z_mm=2.2,first_model_layer_top_z_mm=2.6,vertical_air_gap_mm=.2,
        estimated_seconds=estimate['total_predication'],estimated_grams=sum(f['total_used_g'] for f in estimate['filaments']),
        native_result=result,slicer_warnings=warnings,protected_before=before,protected_after=protected(),
        production_and_A1_unchanged=True,physical_result_pending=True,printer_job_sent=False,
        builder_sha256=sha(Path(__file__)))
    save_json(OUT/'validation.json',report);preview(roof,earlier,chain)
    write_readme(report)
    print(json.dumps(dict(file=str(FINAL),sha256=sha(FINAL),seconds=report['estimated_seconds'],grams=report['estimated_grams'],contact=contact,warnings=warnings),indent=2),flush=True)


def preview(roof,fill,chain):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    fig,ax=plt.subplots(figsize=(8,7))
    for label,ps,c,lw in [('Support roof at Z2.2',roof,'#c6c6c6',.8),('1. Fill printed first at Z2.6',fill,'#dc9220',1.0),('2. First curved wall',chain,'#087c9c',1.8)]:
        ax.add_collection(LineCollection([p['segment'] for p in ps],colors=c,linewidths=lw,label=label))
    ax.autoscale_view();ax.set_aspect('equal');ax.grid(alpha=.2);ax.set_xlabel('Bed X (mm)');ax.set_ylabel('Bed Y (mm)');ax.legend()
    ax.set_title('r3: actual order at the first supported layer')
    fig.tight_layout();fig.savefig(OUT/'print-order-preview.png',dpi=160);plt.close(fig)


def write_readme(r):
    seconds=int(r['estimated_seconds']);m,s=divmod(seconds,60)
    text=f'''DARA A2L PHOTO CURVE - INFILL FIRST - r3
CURRENT TEST: {FINAL.name}
SHA-256: {r['current_sha256']}
Open AS A PROJECT in Bambu Studio. A2L / 0.4 mm nozzle / Textured PEI Plate.
One complete curved photo-lip cutaway, approximately 150.45 x 141.58 x 4.0 mm.
White filament, slot 1. Estimate {m} min {s} sec, {r['estimated_grams']:.2f} g including supports.

WHY THIS TEST
On 2026-10-22 the user reported continuing failure on all previous tests,
including a locally changed standard-support variant, and confirmed that the
curved model perimeter pulls inward while the support stays intact. The local
standard-support project has not been inspected. The reported failure is not
support collapse. R2 did not establish a successful spacing fix.
R2's first curved wall prints before the bridge fill. In this r3 test, Print
infill first changes from OFF to ON. Native G-code confirms bridge fill is
already printed when the long curved wall starts. That gives it potential
lateral contact; adhesion remains a hypothesis requiring a physical result.
Official explanation of this setting (OrcaSlicer; Bambu behavior checked here
directly by native slicing):
https://github.com/OrcaSlicer/OrcaSlicer/wiki/quality_settings_wall_and_surfaces#print-infill-first

ONLY EXPERIMENTAL CHANGE FROM THE R2 RIGHT-HAND PIECE
is_infill_first = 0 -> 1. Wall sequence remains inner wall/outer wall.
Support top interface spacing stays 0.2 mm; two interface layers; top Z gap
stays 0.20 mm. Tree supports are retained from the inspected saved r2 project.
Same entire curve, same 4 mm height, same 2.4 mm recess, same pilot holes and
local screw reinforcement, same orientation and position. The second piece
has been removed to avoid repeating the failed control. The shorter layer
time from printing one object is a practical difference from the paired test.

UNCHANGED PROCESS
8% gyroid, 0.20 mm initial/regular layers, four walls, five top/bottom layers.
Existing screw modifiers remain 100%. White/wood/copper/blue slots and all
filament profiles remain; only white occurs inside the shallow crop.
Bridge 50 mm/s, overhang wall 10 mm/s. Temperature, cooling, flow, brim,
support type, support gaps, purge and other process settings are unchanged.
This test changes model fill order, not support speed or sparse infill density.
Infill-first applies throughout this small test; it has not been promoted to
production, where any effect on finish would need review.

OBSERVE
At layer 13 / Z2.6 mm, verify the short bridge-fill strokes print before the
long curved wall. Watch whether that wall stays curved instead of pulling
across the opening. Photograph it before later layers obscure the result.
Then compare support removal and the underside after cooling. Do not treat
this unprinted revision as a proven correction. No printer job was sent.

PROVENANCE / CHECKS
Production source: {PRODUCTION}
Production SHA-256: {r['source_production_sha256']}
Source plate 2, F2 object 22. Uses the exact r2 right-hand crop and modifiers.
R2 source editable SHA-256: {r['source_r2_editable_sha256']}
Exact XY crop in crop-boundary.geojson; Z0..4.0 mm. Whole curved edge plus short
ends retained (214.17 mm). The crop's production definitions and individual
volume provenance are copied into validation.json.
Full effective global/object/volume settings compared; locked settings checked
in editable, native-sliced project and G-code. Mesh/pose unchanged within
0.001 mm; native bed bounds, support roof height, 0.20 mm air gap, white-only
extrusion, final height, actual speeds and fill-before-wall order checked.
G-code MD5 checksum verified. Only traditional-timelapse compatibility notices
are allowed; no collision or floating-region warnings. Production/A1 hashes
are unchanged. No GUI reopen or physical adhesion qualification was performed.

FILES
{FINAL.name}: current native-sliced test.
{EDIT.name}: matching editable source for the same test.
validation.json, crop-boundary.geojson, print-order-preview.png, SHA256SUMS.txt.
Builder: scripts/build_photo_curve_infill_first.py.
'''
    (OUT/'README.txt').write_text(text,encoding='utf-8')
    files=[FINAL,EDIT,OUT/'validation.json',OUT/'README.txt',OUT/'crop-boundary.geojson',OUT/'print-order-preview.png',OUT/'saved-plate_1.png',OUT/'saved-top_1.png']
    (OUT/'SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in files),encoding='utf-8')


if __name__=='__main__':run()
