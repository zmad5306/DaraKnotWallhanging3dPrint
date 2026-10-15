"""Verify native output, merge changed plates, then publish the mirrored release."""
from build_mirrored_project import *
from validate_print_project import TOKEN
from review_curve_artifacts import arc_samples
from shapely import contains,points

def parsed(files):
    cfg=ET.fromstring(files['Metadata/model_settings.config']);root=ET.fromstring(files['3D/3dmodel.model'])
    return cfg,root,{props(o)['name'].split(' - ')[0]:o for o in cfg.findall('object')}

def entries(files,parsed,name):
    cfg,root,configs=parsed;co=configs[name];oid=co.get('id');top=root.find(tag('resources')).find(f"{tag('object')}[@id='{oid}']")
    bi=next(b for b in root.find(tag('build')) if b.get('objectid')==oid);rows=[];children={}
    for part in co.findall('part'):
        comp=next(c for c in top.find(tag('components')) if c.get('objectid')==part.get('id'));path=comp.get('{'+P+'}path').lstrip('/')
        if path not in children:children[path]=ET.fromstring(files[path])
        obj=children[path].find(tag('resources')).find(f"{tag('object')}[@id='{part.get('id')}']")
        mesh=read_mesh(obj);mesh.apply_transform(transform(bi.get('transform'))@transform(comp.get('transform')))
        paint=[int(t.get('paint_supports','0'),16) for t in obj.find(tag('mesh')).find(tag('triangles'))]
        rows.append(dict(part=part,mesh=mesh,paint=paint))
    return rows

def support_centers(text):
    x=y=z=e=0.;feature='Custom';relative=False;xyzrelative=False;result=[]
    for raw in text.splitlines():
        if raw.startswith('; FEATURE: '):feature=raw[11:].strip()
        code=raw.split(';',1)[0].strip()
        if not code:continue
        cmd=code.split()[0]
        if cmd=='M83':relative=True
        elif cmd=='M82':relative=False
        elif cmd in ('G90','G91'):xyzrelative=cmd=='G91'
        elif cmd=='G92':
            v={k:float(n) for k,n in TOKEN.findall(code)};x,y,z,e=[v.get(k,old) for k,old in zip('XYZE',(x,y,z,e))]
        elif cmd in ('G0','G1','G2','G3'):
            v={k:float(n) for k,n in TOKEN.findall(code)}
            nx,ny,nz=[old+v.get(k,0) if xyzrelative else v.get(k,old) for k,old in zip('XYZ',(x,y,z))]
            de=v.get('E',0) if relative else v.get('E',e)-e
            if de>0 and feature=='Support interface' and any(k in v for k in ('X','Y','I','J')):
                if cmd in ('G2','G3'):
                    xy=arc_samples((x,y),(nx,ny),v,cmd=='G3')
                    result.extend(np.column_stack([xy,np.linspace(z,nz,len(xy))]).tolist())
                else:result.extend([[x,y,z],[(x+nx)/2,(y+ny)/2,(z+nz)/2],[nx,ny,nz]])
            x,y,z=nx,ny,nz;e=e+v.get('E',0) if relative else v.get('E',e)
    return np.array(result)

def verify_and_merge():
    stage=json.loads((WORK/'project-stage.json').read_text());geometry=json.loads((REVIEW/'geometry-validation.json').read_text())
    assert sha(WORK/'staged.3mf')==stage['staged_sha256'];assert sha(CAD)==geometry['source_sha256']
    result=json.loads((WORK/'slice/result.json').read_text());assert result['return_code']==0 and len(result['sliced_plates'])==32,result
    baseline=read_zip(BASE/'Dara.3mf');files=read_zip(WORK/'staged.3mf');native=read_zip(WORK/'slice/sliced.3mf')
    sp=parsed(files);np_=parsed(native);bp=parsed(baseline)
    assert len(sp[2])==len(np_[2])==47 and len(np_[1].find(tag('build')))==78
    changed_ids=set(stage['changed_object_ids']);paths=set(stage['changed_mesh_paths'])
    allowed=paths|{'3D/3dmodel.model','Metadata/model_settings.config','Metadata/project_settings.config'}
    assert {k for k in files if files[k]!=baseline[k]}<=allowed
    oldsettings=json.loads(baseline['Metadata/project_settings.config']);settings=json.loads(files['Metadata/project_settings.config'])
    assert {k for k in settings if settings[k]!=oldsettings[k]}=={'wipe_tower_x','wipe_tower_y'}
    ns=json.loads(native['Metadata/project_settings.config'])
    assert all(ns.get(k)==v for k,v in settings.items()),{k:(v,ns.get(k)) for k,v in settings.items() if ns.get(k)!=v}
    for name,co in sp[2].items():
        if co.get('id') not in changed_ids:
            assert xml(co)==xml(bp[2][name]),name
            oldid=bp[2][name].get('id')
            assert [xml(b) for b in sp[1].find(tag('build')) if b.get('objectid')==oldid]==[xml(b) for b in bp[1].find(tag('build')) if b.get('objectid')==oldid]
    info=ET.fromstring(baseline['Metadata/slice_info.config']);ni=ET.fromstring(native['Metadata/slice_info.config'])
    checks=[];roundtrip=[];h=json.loads((WORK/'hammered-stage.json').read_text())
    for n in CHANGED:
        name=f'F{n}' if n<=20 else f'M{n-20}'
        aa=entries(native,np_,name);ee=entries(files,sp,name);assert len(aa)==len(ee),(name,len(aa),len(ee))
        for a,e in zip(aa,ee):
            assert a['part'].get('subtype')==e['part'].get('subtype')
            av,ev=a['mesh'].vertices,e['mesh'].vertices
            err=max(cKDTree(av).query(ev)[0].max(),cKDTree(ev).query(av)[0].max());assert err<.0002,(name,err)
            for k,v in props(e['part']).items():
                if k.startswith('source_') or k=='matrix':continue
                if k=='extruder':assert props(a['part']).get(k,props(np_[2][name]).get(k))==v,(name,k)
                else:assert props(a['part']).get(k)==v,(name,k)
            assert {s:a['paint'].count(s) for s in [4,8]}=={s:e['paint'].count(s) for s in [4,8]},name
            roundtrip.append(dict(name=name,part=props(e['part'])['name'],max_vertex_error_mm=float(err)))
        stat=next(p for p in ni.findall('plate') if int(props(p)['index'])==n);values=props(stat)
        assert values['outside']=='false' and values['pause_count']=='0',(n,values)
        warnings=[w.attrib for w in stat.findall('warning')];assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings),(n,warnings)
        plate=next(p for p in sp[0].findall('plate') if int(props(p)['plater_id'])==n)
        assert {o.get('identify_id') for o in stat.findall('object')}=={props(i)['identify_id'] for i in plate.findall('model_instance')}
        gc=native[f'Metadata/plate_{n}.gcode'];text=gc.decode();assert hashlib.md5(gc).hexdigest()==native[f'Metadata/plate_{n}.gcode.md5'].decode().strip().lower()
        audit=scan_gcode(text);zs=audit.pop('model_extrusion_z_by_filament_mm');audit['model_z_ranges_mm']={k:[min(v),max(v)] for k,v in zs.items()}
        assert audit['conservative_bed_edge_clearance_mm']>=.3,(name,audit['bead_xy_bounds_mm'])
        assert set(zs)==({'1','2','4'} if n<=20 else {'3'}),(name,zs.keys())
        if n<=20:
            assert min(zs['4'])>=13.19 and max(zs['4'])<=13.61,(name,zs['4'])
            assert min(zs['2'])>=8.59 and max(zs['2'])<=10.01,(name,zs['2'])
        assert 'M201 X1000 Y1000 Z1500 E5000' in text and 'M203 X150 Y150 Z30 E30' in text
        assert not re.search(r'^\s*(?:M400\s+U1|M0(?:\s|$)|M1(?:\s|$)|M25(?:\s|$))',text,re.M)
        if n>20:
            for feature in ['Support','Support interface']:assert audit['features'].get(feature,0)>0
            centers=support_centers(text);assert len(centers)>0
            pi=n-1;world=centers+[pi%6*307.2,-(pi//6)*307.2,0]
            local=trimesh.transform_points(world,np.linalg.inv(h['poses'][name]['assembly_to_world']))
            data=np.load(WORK/'hammered'/(name+'-changed.npz'));body=trimesh.Trimesh(data['vertices'],data['faces'],process=False)
            inside=contains(mesh_slice(body,9).buffer(-.6),points(local[:,:2]));maximum=float(local[inside,2].max()) if inside.any() else None
            assert maximum is None or maximum<8.5,(name,maximum)
            audit['support_interface_check']=dict(samples=len(local),interior_samples=int(inside.sum()),maximum_interior_assembly_z_mm=maximum,visible_surface_starts_at_mm=9.9)
        for key,value in native.items():
            if re.fullmatch(r'Metadata/(?:plate_'+str(n)+r'(?:_small)?|plate_no_light_'+str(n)+r'|top_'+str(n)+r'|pick_'+str(n)+r')\.(?:png|json|gcode(?:\.md5)?)',key):files[key]=value
        replacement=copy.deepcopy(stat);setmeta(replacement,'printer_model_id','N2S')
        original=next(p for p in info.findall('plate') if int(props(p)['index'])==n);at=list(info).index(original);info.remove(original);info.insert(at,replacement)
        audit.update(plate=n,gcode_sha256=hashlib.sha256(gc).hexdigest(),weight_g=float(values['weight']),seconds=int(values['prediction']))
        checks.append(audit);print('Verified plate',n,'edge clearance',round(audit['conservative_bed_edge_clearance_mm'],3),flush=True)
    files['Metadata/slice_info.config']=xml(info)
    sequence=json.loads(baseline['Metadata/filament_sequence.json']);newsequence=json.loads(native['Metadata/filament_sequence.json'])
    for n in CHANGED:
        key=f'plate_{n}'
        if key in newsequence:sequence[key]=newsequence[key]
    files['Metadata/filament_sequence.json']=json.dumps(sequence).encode()
    unchanged=[];estimates=[]
    for plate in info.findall('plate'):
        values=props(plate);n=int(values['index']);estimates.append(dict(plate=n,weight_g=float(values['weight']),seconds=int(values['prediction'])))
        if n not in CHANGED:
            key=f'Metadata/plate_{n}.gcode';assert files[key]==baseline[key]
            unchanged.append(dict(plate=n,gcode_sha256=hashlib.sha256(files[key]).hexdigest()))
    output=WORK/'release.3mf';write_zip(output,files)
    with zipfile.ZipFile(output) as z:assert z.testzip() is None
    report=dict(project_sha256=sha(output),baseline_sha256=stage['baseline_sha256'],source_cad_sha256=sha(CAD),plates=32,objects=47,instances=78,
        changed_plates=checks,unchanged_native_plates=unchanged,mesh_checks=stage['hammered_checks'],native_roundtrip_checks=roundtrip,
        geometry_checks=geometry,tower_placements=stage['towers'],precision_settings={'enable_arc_fitting':'1','resolution':'0.05'},
        total_weight_g=round(sum(r['weight_g'] for r in estimates),2),total_seconds=sum(r['seconds'] for r in estimates),all_plate_estimates=estimates,
        physical_test_pending=True,scope='20 mirrored frame sections and three matching hammered M rear attachments. Nine other saved slices and all other meshes unchanged.',
        preserved_cover_report='cover-crown-validation.json',seam_count=32,hardware_moves=json.loads(PLAN.read_text())['hardware_moves'])
    (REVIEW/'release-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    # Compatibility input for the independent arc review.
    (WORK/'perimeter-input.json').write_text(json.dumps(dict(plate_layout=[dict(items=[dict(xy=[128,128])]) for _ in range(32)])))
    print('Validated candidate ready for the independent perimeter check.',flush=True)

def publish():
    report=json.loads((REVIEW/'release-validation.json').read_text());edge=json.loads((REVIEW/'perimeter-review.json').read_text())
    assert sha(WORK/'release.3mf')==report['project_sha256']==edge['project_sha256'];assert edge['summary']['passed']
    assert edge['summary']['perimeter_arcs_checked']>100 and edge['summary']['large_arcs_covered']>=50,edge['summary']
    report['perimeter_review']=edge['summary']
    opened=json.loads((WORK/'release-open/validation.json').read_text())
    assert opened['input_sha256']==report['project_sha256'] and opened['exit_code']==0
    report['complete_package_native_open']=opened
    for target in [ROOT/'Dara.3mf',PACKAGE/'Dara-Photo-Frame-A1-Complete.3mf']:
        assert sha(target)==report['baseline_sha256'];shutil.copy2(WORK/'release.3mf',target);assert sha(target)==report['project_sha256']
    (PACKAGE/'mirrored-joints-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    (REVIEW/'release-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Published both verified production projects.',flush=True)

def check_open():
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe');out=WORK/'release-open';out.mkdir(exist_ok=True)
    result=subprocess.run([str(exe),'--export-3mf','roundtrip.3mf','--outputdir',str(out),str(WORK/'release.3mf')],cwd=exe.parent,creationflags=subprocess.CREATE_NO_WINDOW)
    result.check_returncode()
    with zipfile.ZipFile(out/'roundtrip.3mf') as z:assert z.testzip() is None
    proof=dict(input_sha256=sha(WORK/'release.3mf'),exit_code=result.returncode,roundtrip_sha256=sha(out/'roundtrip.3mf'))
    (out/'validation.json').write_text(json.dumps(proof,indent=2)+'\n');print('Complete release opens and saves in native Bambu Studio.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['verify','check-open','publish']);a=p.parse_args();{'verify':verify_and_merge,'check-open':check_open,'publish':publish}[a.action]()
