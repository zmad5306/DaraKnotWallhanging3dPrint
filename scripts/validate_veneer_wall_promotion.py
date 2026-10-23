"""Verify the three replacement plates and byte preservation of all others."""
import copy,hashlib,json,re,sys
import xml.etree.ElementTree as ET
from promote_veneer_wall_cradle import *
from check_fin_toolpaths import check_fin_bonds
from check_veneer_wall_openings import check_openings
from check_a2l_towers import check_startup_tower
from shapely.geometry import MultiPoint
CORRECTION_GEOMETRY=None


def digest(data):return hashlib.sha256(data).hexdigest()


def path_signature(text):
    # Feature tags and every executable line except object-label identifiers.
    # Includes all moves, extrusion modes, temperatures, cooling and commands.
    lines=[]
    for line in text.splitlines():
        if line.startswith('; FEATURE:'):lines.append(line)
        code=line.split(';',1)[0].strip()
        if code and code.split()[0] not in ['M624','M625']:lines.append(code)
    return digest('\n'.join(lines).encode())


def run():
    original=read(BASE/'Dara.3mf');current=read(NATIVE/'sliced.3mf');editable=read(EDIT)
    patch=json.loads((WORK/'geometry-patch.json').read_text())
    review=json.loads((REVIEW/'validation.json').read_text()) if CORRECTION_GEOMETRY is None else None
    assert sha(EDIT)==patch['editable']['target_sha256']
    assert current['Metadata/project_settings.config']==original['Metadata/project_settings.config']
    settings=json.loads(current['Metadata/project_settings.config'])
    # Studio normalizes legacy editable spellings/defaults on save. Preserve
    # both source containers byte-for-byte; the newly sliced effective native
    # settings were compared to the original native settings during merging.
    baseline_editable=read(BASE/OUT.relative_to(ROOT)/'Dara-A2L-Editable.3mf')
    assert editable['Metadata/project_settings.config']==baseline_editable['Metadata/project_settings.config']
    for key,value in dict(sparse_infill_density='8%',sparse_infill_pattern='gyroid',layer_height='0.2',
        initial_layer_print_height='0.2',wall_loops='4',top_shell_layers='5',bottom_shell_layers='5',
        curr_bed_type='Textured PEI Plate',printer_model='Bambu Lab A2L').items():assert settings[key]==value
    assert settings['nozzle_diameter']==['0.4']
    assert current['3D/3dmodel.model']==original['3D/3dmodel.model']
    oldcfg=ET.fromstring(original['Metadata/model_settings.config']);cfg=ET.fromstring(current['Metadata/model_settings.config'])
    oldinfo=ET.fromstring(original['Metadata/slice_info.config']);info=ET.fromstring(current['Metadata/slice_info.config'])
    oldseq=json.loads(original['Metadata/filament_sequence.json']);seq=json.loads(current['Metadata/filament_sequence.json'])
    allowed=set(patch['native']['changed_child_assets'])|{'Metadata/model_settings.config','Metadata/slice_info.config','Metadata/filament_sequence.json'}
    allowed.update(n for n in current if any(plate_asset(n,i) for i in CHANGED))
    assert current.keys()==original.keys()
    for name,data in original.items():
        if name not in allowed:assert current[name]==data,name
    changed_ids={props(oldcfg.findall('plate')[i-1].find('model_instance'))['object_id'] for i in CHANGED}
    for old,new in zip(oldcfg.findall('object'),cfg.findall('object')):
        if old.get('id') not in changed_ids:assert ET.tostring(old)==ET.tostring(new)
        else:
            assert {k:v for k,v in props(old).items() if k not in [None,'name']}=={k:v for k,v in props(new).items() if k not in [None,'name']}
            a,b=old.find('part'),new.find('part')
            assert a.attrib==b.attrib
            assert {k:v for k,v in props(a).items() if k!='name'}=={k:v for k,v in props(b).items() if k!='name'}
    kept=[]
    for number in range(1,21):
        key=f'Metadata/plate_{number}.gcode';raw=current[key]
        assert hashlib.md5(raw).hexdigest()==current[key+'.md5'].decode().strip().lower()
        if number in CHANGED:continue
        assert ET.tostring(oldcfg.findall('plate')[number-1])==ET.tostring(cfg.findall('plate')[number-1])
        a=next(p for p in oldinfo.findall('plate') if props(p)['index']==str(number))
        b=next(p for p in info.findall('plate') if props(p)['index']==str(number))
        assert ET.tostring(a)==ET.tostring(b)
        assert seq[f'plate_{number}']==oldseq[f'plate_{number}']
        assets={n:digest(v) for n,v in original.items() if plate_asset(n,number)}
        for n,h in assets.items():assert digest(current[n])==h,n
        kept.append(dict(plate=number,geometry_settings_and_poses_unchanged=True,gcode_byte_identical=True,preserved_assets_sha256=assets))
    # Editable counterpart also changes only the recorded three mesh assets
    # and the names/counts of their existing objects/plates.
    oldedit=read(BASE/OUT.relative_to(ROOT)/'Dara-A2L-Editable.3mf')
    for name,data in oldedit.items():
        if name not in set(patch['editable']['changed_child_assets'])|{'Metadata/model_settings.config'}:assert editable[name]==data,name
    native_report=json.loads((BASE/OUT.relative_to(ROOT)/'native-validation.json').read_text())
    result=json.loads((NATIVE/'result.json').read_text());rows=[]
    for number in sorted(CHANGED):
        i=number-14
        actual_native=read(WORK/f'plate-{number}/sliced.3mf')
        if CORRECTION_GEOMETRY is None:
            review_row=review['plates'][i-1];file_record=review['files'][i-1]
            approved=REVIEW/Path(file_record['final_file']).name
            assert sha(approved)==file_record['final_sha256']
            one=read(approved)
            comparison=vertices(selected(one,1)[5])@selected(one,1)[6][:3,:3].T+selected(one,1)[6][:3,3]
        else:
            comparison=np.load(CORRECTION_GEOMETRY/f'V{i}-candidate.npz')['vertices']
        poses=[];names=[]
        for files,plate in [(editable,number),(current,number),(actual_native,number)]:
            _,_,obj,_,_,m,t=selected(files,plate)
            poses.append(vertices(m)@t[:3,:3].T+t[:3,3]);names.append(props(obj)['name'])
        errors=[max(float(cKDTree(comparison).query(p)[0].max()),float(cKDTree(p).query(comparison)[0].max())) for p in poses]
        assert max(errors)<.001,errors
        # Matching triangles retain the reviewed show-face support painting.
        if CORRECTION_GEOMETRY is None:
            actual_mesh=selected(editable,number)[5]
            review_mesh=selected(read(REVIEW/Path(file_record['editable_file']).name),1)[5]
            assert [t.attrib for t in actual_mesh.find(tag('triangles'))]==[t.attrib for t in review_mesh.find(tag('triangles'))]
        else:
            assert all(x['saved_support_paint_rule_verified'] for x in patch['editable']['support_painting'])
            assert all(x['saved_support_paint_rule_verified'] for x in patch['native']['support_painting'])
        raw=current[f'Metadata/plate_{number}.gcode'];text=raw.decode()
        gcode_settings=dict(re.findall(r'^; ([A-Za-z_0-9]+) = (.*)$',text,re.MULTILINE))
        locked=dict(sparse_infill_density='8%',sparse_infill_pattern='gyroid',layer_height='0.2',
            initial_layer_print_height='0.2',wall_loops='4',top_shell_layers='5',bottom_shell_layers='5',
            curr_bed_type='Textured PEI Plate',nozzle_diameter='0.4')
        assert all(gcode_settings.get(k)==value for k,value in locked.items())
        signature=path_signature(text);same_paths=CORRECTION_GEOMETRY is None and signature==path_signature(one['Metadata/plate_1.gcode'].decode())
        scan=scan_gcode(text);low,high=np.array(scan['bead_xy_bounds_mm'])
        clearance=float(min(*low,*(np.array([330,320])-high)));assert clearance>.5
        assert set(scan['model_extrusion_z_by_filament_mm'])=={'3'}
        assert max(scan['model_extrusion_z_by_filament_mm']['3'])<=325
        expected=review_row['geometry'] if CORRECTION_GEOMETRY is None else json.loads((CORRECTION_GEOMETRY/f'V{i}-geometry.json').read_text())
        if same_paths:
            bonds=review_row['bond_toolpath_check'];openings=review_row['opening_toolpath_checks']
            bands=review_row['grounded_wall_toolpath_checks']['bands']
        else:
            bonds=check_fin_bonds(text,expected);openings=check_openings(text,expected['openings'])
            probes=[]
            for band in expected['bed_tie_bands']:
                xmin,xmax=band['x_span_mm'];half=band['width_mm']/2
                for height in [.2,.4,.6]:
                    for offset in [-half+.3,0,half-.3]:
                        probes.extend([[float(x),band['center_y_mm']+offset,height] for x in np.linspace(xmin+.6,xmax-.6,max(3,int((xmax-xmin)/10)+1))])
            bands=check_fin_bonds(text,{'bond_probes_print_xyz_mm':probes},layer_tolerance_mm=.01)
        plate_info=next(p for p in info.findall('plate') if props(p)['index']==str(number))
        warnings=[w.attrib for w in plate_info.findall('warning')]
        assert all(w['msg']=='not_support_traditional_timelapse' for w in warnings)
        estimate=result['sliced_plates'][number-1];weight=sum(f['total_used_g'] for f in estimate['filaments'])
        scan.update(plate=number,gcode_sha256=digest(raw),weight_g=weight,seconds=estimate['total_predication'],
            conservative_bed_edge_clearance_mm=clearance,bonded_fin_toolpaths=bonds,
            maximum_model_extrusion_z_mm=max(scan['model_extrusion_z_by_filament_mm']['3']),
            startup_prime_tower_check=check_startup_tower(settings,[MultiPoint(poses[1][:,:2]).convex_hull],1,float(poses[1][:,2].max()),number))
        scan.pop('model_extrusion_z_by_filament_mm');native_report['plates'][number-1]=scan
        old_name=native_report['native_roundtrip'][next(k for k,r in enumerate(native_report['native_roundtrip']) if r['name'].startswith(f'V{i} A2L'))]['name']
        for record in native_report['native_roundtrip']:
            if record['name']==old_name:record.update(name=names[0],maximum_vertex_and_pose_error_mm=max(errors),distance_metric='bidirectional comparison to the saved candidate mesh in printer coordinates')
        rows.append(dict(plate=number,veneer=f'V{i}',name=names[0],weight_g=weight,seconds=estimate['total_predication'],
            bounds_mm=[poses[1].min(axis=0).tolist(),poses[1].max(axis=0).tolist()],maximum_mesh_error_mm=max(errors),
            reviewed_native_sha256=sha(approved) if CORRECTION_GEOMETRY is None else None,reviewed_geometry=expected,reviewed_toolpath_signature_identical=same_paths,
            executable_and_feature_signature=signature,gcode_sha256=digest(raw),gcode_locked_settings=locked,
            bond_toolpaths=bonds,band_toolpaths=bands,opening_toolpaths=openings,native_warnings=warnings))
        print(f'Validated plate {number}: {weight:.2f} g; reviewed executable paths identical: {same_paths}',flush=True)
    total=sum(p['weight_g'] for p in rows);assert total<1000
    external=json.loads((WORK/'protected.json').read_text())
    for name,h in external.items():assert sha(ROOT/name)==h
    preservation=dict(baseline_project_sha256=EXPECTED_SOURCE,project_sha256=sha(NATIVE/'sliced.3mf'),plates=kept,
        editable_sha256=sha(EDIT),baseline_editable_sha256=patch['editable']['source_sha256'],protected_external_file_sha256=external,changed_plates=sorted(CHANGED),
        unchanged_model_graph_and_global_settings=True,all_other_zip_entries_byte_preserved=True)
    proof=dict(revision=REVISION,source_sha256=EXPECTED_SOURCE,project_sha256=sha(NATIVE/'sliced.3mf'),editable_sha256=sha(EDIT),
        approved_review_validation_sha256=sha(REVIEW/'validation.json') if CORRECTION_GEOMETRY is None else None,plates=rows,total_veneer_and_support_g=total,
        headroom_to_1000g=1000-total,total_seconds=sum(r['seconds'] for r in rows),physical_confirmation_pending=True,
        user_approved_production_promotion=True)
    native_report.update(editable_sha256=sha(EDIT),native_project_sha256=sha(NATIVE/'sliced.3mf'),slicer_result=result,
        veneer_carrier_revision=REVISION,preserved_plate_validation_basis='veneer-wall-unchanged-plates.json')
    save_json(WORK/'veneer-wall-unchanged-plates.json',preservation)
    save_json(WORK/'veneer-wall-promotion-validation.json',proof)
    save_json(WORK/'native-validation.json',native_report)
    print(f'All three veneers and supports: {total:.2f} g. Other 17 plates preserved.',flush=True)


if __name__=='__main__':run()
