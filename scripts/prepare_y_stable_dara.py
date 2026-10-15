"""Reorient copper plates along the bed's Y travel, re-slice and audit Dara.

Keep the assembled geometry, scale, joint cuts and color regions unchanged.
Motion limits are written as slicer settings, never patched into G-code.
"""
import argparse,copy,json,hashlib,math,re,shutil,subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
import prepare_hammered_bands as b
from integrate_hammered_dara import selected_entries,plate_offset,TARGETS,PACKAGE,digest
from y_axis_orientation import choose,center,rot,TRAVEL,COPPER,BAND_CENTERS,TEST_CENTERS
from validate_print_project import TOKEN

ROOT=b.ROOT;WORK=ROOT/'.work/y-stable-dara';REVIEW=ROOT/'working/review/y-stable-dara'
SOURCES={'normal':ROOT/'Dara.3mf','test':b.TEST,'candidate':b.TARGET}
COUNTS={'normal':32,'test':1,'candidate':7}
MPLATES=[21,22,23,24,25,26,31]


def snapshot():
    WORK.mkdir(parents=True,exist_ok=True);REVIEW.mkdir(parents=True,exist_ok=True)
    expected={
        'normal':json.loads((PACKAGE/'knot-glue-sample-validation.json').read_text())['project_sha256'],
        'test':json.loads((b.REVIEW/'test-validation.json').read_text())['sha256'],
        'candidate':json.loads((b.REVIEW/'full-validation.json').read_text())['sha256']}
    for kind,path in SOURCES.items():
        assert b.sha(path)==expected[kind],f'{kind}: this migration expects the pre-Y-alignment release; refusing to reinterpret a changed orientation.'
        dest=WORK/(kind+'-baseline.3mf')
        if not dest.exists():shutil.copy2(path,dest)
        assert b.sha(dest)==b.sha(path),'Source changed since staging.'


def recover(body,rotation,bounds):
    t=b.np.eye(4);t[:3,:3]=rotation[:3,:3].T
    pts=body.vertices@t[:3,:3].T
    t[:3,3]=b.np.array(bounds).mean(axis=0)-(pts.min(axis=0)+pts.max(axis=0))/2
    return t


def stage():
    snapshot()
    manifest=json.loads((b.REVIEW/'geometry-validation.json').read_text())
    rows={r['name']:r for r in manifest['parts']}
    full=selected_entries(b.read_zip(SOURCES['normal']),{f'M{i}' for i in range(1,7)}|{f'Band{i}' for i in range(1,6)})
    assembly={};new_transforms={};choices={}
    for name,parts in full.items():
        canonical=name.replace('Band','B');r=rows[canonical]
        undo=recover(parts[0]['mesh'],b.np.array(r['build_transform']),r['bounds_mm'])
        m=parts[0]['mesh'].copy();m.apply_transform(undo);assembly[canonical]=m
        t,size,angle=choose(m);new_transforms[canonical]=t
        choices[canonical]=dict(in_plane_rotation_deg=angle,build_extent_mm=size,build_transform=t.tolist(),
                               old_yaw_deg=r['yaw_deg'],old_build_extent_mm=r['print_extent_mm'])
    # Crops retain the exact actual production parent orientation in the test.
    j=b.layout()[2][0];crop=b.prism(b.locate(b.rect(-10,-35,27,35),j[2],j[3]),20,-1)
    for n in [2,3]:assembly[f'T{n}']=b.boolean([assembly[f'M{n}'],crop],'intersection')
    cad=b.CAD.read_text();holes=[(kind,h[2]) for kind,key in [('screw','screw_mounts'),('locator','dowel_mounts')] for h in b.read_array(cad,key)]
    for kind,path in SOURCES.items():
        files=b.read_zip(WORK/(kind+'-baseline.3mf'));root=ET.fromstring(files['3D/3dmodel.model']);cfg=ET.fromstring(files['Metadata/model_settings.config'])
        names=set(full) if kind=='normal' else set(assembly) - ({'T2','T3'} if kind=='candidate' else {f'M{i}' for i in range(1,7)}|{f'B{i}' for i in range(2,6)})
        entries=selected_entries(files,names);configs={b.props(o)['name'].split(' - ')[0]:o for o in cfg.findall('object')}
        build={i.get('objectid'):i for i in root.find(b.tag('build'))}
        resources={o.get('id'):o for o in root.find(b.tag('resources'))}
        object_plate={b.props(i)['object_id']:int(b.props(p)['plater_id']) for p in cfg.findall('plate') for i in p.findall('model_instance')}
        modified=[]
        for name,parts in entries.items():
            canonical=name.replace('Band','B');parent=canonical.replace('T','M')
            co=configs[name];oid=co.get('id');n=object_plate[oid]
            oldR=b.COMMON if kind=='test' else b.np.array(rows[canonical]['build_transform'])
            undo=recover(parts[0]['mesh'],oldR,assembly[canonical].bounds)
            original=parts[0]['mesh'].copy();original.apply_transform(undo)
            ref=assembly[canonical]
            error=max(b.cKDTree(ref.vertices).query(original.vertices)[0].max(),b.cKDTree(original.vertices).query(ref.vertices)[0].max())
            if canonical.startswith('T'):
                # Re-cutting the rounded native parent can retriangulate flat
                # faces. Compare the solids, not those extra coplanar vertices.
                difference=b.boolean([original,ref],'difference').volume+b.boolean([ref,original],'difference').volume
                assert abs(original.bounds-ref.bounds).max()<.0002 and difference<.1,(kind,name,difference)
                error=None
            else:assert error<.0002,(kind,name,error)
            t=new_transforms[parent]
            xy=(128,128)
            if canonical.startswith('B'):xy=BAND_CENTERS[int(canonical[1:])-1]
            if kind=='test':xy=TEST_CENTERS[['T2','T3','B1'].index(canonical)]
            t=center(original,t,xy)
            item=build[oid];oldB=b.transform(item.get('transform'))
            offset=plate_offset(n,6 if kind=='normal' else 3)
            world=t.copy();world[:2,3]+=offset
            newB=world@undo@oldB
            item.set('transform',' '.join(f'{v:.12g}' for v in newB[:3,:].T.ravel()))
            for k,v in COPPER.items():b.setmeta(co,k,v)
            # Repaint only support eligibility, using the unchanged mesh faces.
            obj=resources[oid];comp=list(obj.find(b.tag('components')))[0]
            childpath=comp.get('{'+b.P+'}path').lstrip('/');child=ET.fromstring(files[childpath])
            meshobj=child.find(b.tag('resources')).find(f"{b.tag('object')}[@id='{comp.get('objectid')}']")
            normals=original.face_normals;placed_normals=normals@t[:3,:3].T;centers=original.triangles_center
            hm=b.np.zeros(len(normals),bool)
            if not canonical.startswith('B'):
                for hkind,xyh in holes:hm|=(b.np.linalg.norm(centers[:,:2]-xyh,axis=1)<(1.75 if hkind=='screw' else 3.05))&(centers[:,2]<(8.71 if hkind=='screw' else 3.4))
            front=(normals[:,2]>-.01) if canonical.startswith('B') else (original.triangles[:,:,2].max(axis=1)>9.89)
            enforce=(placed_normals[:,2]<-.1)&~front&~hm;block=front|hm
            triangles=meshobj.find(b.tag('mesh')).find(b.tag('triangles'))
            assert len(triangles)==len(normals)
            for i,tri in enumerate(triangles):
                tri.attrib.pop('paint_supports',None)
                if block[i] or enforce[i]:tri.set('paint_supports','8' if block[i] else '4')
            files[childpath]=b.xml(child)
            normal=t[:3,2];assert abs(normal[1])<1e-10 and abs(normal[2]-math.cos(math.radians(55)))<1e-10
            modified.append(dict(name=name,canonical=canonical,plate=n,build_transform=t.tolist(),undo_original_world=undo.tolist(),
                                 show_face_normal=normal.tolist(),source_error_mm=None if error is None else float(error),enforced_facets=int(enforce.sum()),blocked_facets=int(block.sum())))
        settings=json.loads(files['Metadata/project_settings.config']);settings.update(TRAVEL)
        settings['print_settings_id']='Dara A1 - Y aligned copper - gentle bed travel'
        files.update({'3D/3dmodel.model':b.xml(root),'Metadata/model_settings.config':b.xml(cfg),'Metadata/project_settings.config':json.dumps(settings,indent=2).encode()})
        b.write_zip(WORK/(kind+'-staged.3mf'),files)
        report=dict(kind=kind,baseline_sha256=b.sha(path),objects=modified,choices=choices,travel_settings=TRAVEL,copper_overrides=COPPER)
        (WORK/(kind+'-stage.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(kind,'staged',len(modified),'copper objects',flush=True)
    print(json.dumps(choices,indent=2),flush=True)


def slice_project(kind):
    out=WORK/(kind+'-slice');out.mkdir(exist_ok=True)
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    with (out/'cli.log').open('w') as log:
        result=subprocess.run([str(exe),'--slice','0','--export-3mf','sliced.3mf','--outputdir',str(out),str(WORK/(kind+'-staged.3mf'))],
                              cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode==0,(kind,result.returncode)
    print(kind,'native slicing completed',flush=True)


def motion_audit(text):
    """Check commanded moving-bed speeds/accelerations during sliced layers.

    Startup calibration/purge and shutdown custom routines are excluded.
    The values are commanded caps, not measured printer acceleration.
    """
    feature='Custom';x=y=z=e=0.;relative=False;xyzrelative=False;feed=0.;acc=0.;counts={};maxima={}
    started=False;skipping=False;ended=False;axis_commands=[]
    for raw in text.splitlines():
        if raw.startswith('; CHANGE_LAYER'):started=True
        if raw.startswith('; SKIPPABLE_START'):skipping=True
        if raw.startswith('; SKIPPABLE_END'):skipping=False
        if raw.startswith('; close powerlost recovery'):ended=True
        if raw.startswith('; FEATURE: '):feature=raw[11:].strip()
        code=raw.split(';',1)[0].strip()
        if not code:continue
        cmd=code.split()[0]
        if cmd in ['M201','M203']:
            axis_commands.append(code)
        if cmd=='M204':
            match=re.search(r'\bS([\d.]+)',code)
            if match:acc=float(match[1])
        elif cmd=='M83':relative=True
        elif cmd=='M82':relative=False
        elif cmd in ['G90','G91']:xyzrelative=cmd=='G91'
        elif cmd=='G92':
            v={k:float(n) for k,n in TOKEN.findall(code)};x,y,z,e=[v.get(k,old) for k,old in zip('XYZE',(x,y,z,e))]
        elif cmd in ['G0','G1','G2','G3']:
            v={k:float(n) for k,n in TOKEN.findall(code)}
            nx,ny,nz=[old+v.get(k,0) if xyzrelative else v.get(k,old) for k,old in zip('XYZ',(x,y,z))]
            de=v.get('E',0) if relative else v.get('E',e)-e;feed=v.get('F',feed)
            if started and not skipping and not ended and feature!='Custom' and (abs(ny-y)>1e-5 or ('J' in v)):
                category='extrusion' if de>0 else 'travel'
                maxima[category+'_acceleration']=max(maxima.get(category+'_acceleration',0),acc)
                maxima[category+'_speed']=max(maxima.get(category+'_speed',0),feed/60)
                counts[category]=counts.get(category,0)+1
            x,y,z=nx,ny,nz;e=e+v.get('E',0) if relative else v.get('E',e)
    y_accel=[float(re.search(r'Y([\d.]+)',c)[1]) for c in axis_commands if c.startswith('M201 ') and 'Y' in c]
    y_speed=[float(re.search(r'Y([\d.]+)',c)[1]) for c in axis_commands if c.startswith('M203 ') and 'Y' in c]
    bounded={k:min(v,max(y_accel if k.endswith('acceleration') else y_speed)) for k,v in maxima.items()} if y_accel and y_speed else {}
    return dict(commanded_maxima=maxima,y_axis_upper_bounds=bounded,checked_y_moves=counts,axis_limit_commands=axis_commands,
                conditional_routine_note='A conditional inspection can leave M204 S5000 active until a role change. M201 X1000 Y1000 supplies an independent per-axis cap; this is commanded configuration, not measured motion.',
                excludes='Startup, shutdown, conditional firmware inspection/timelapse and custom filament routines. Axis caps are checked separately.')


def verify(kind):
    stageinfo=json.loads((WORK/(kind+'-stage.json')).read_text())
    reference=b.read_zip(WORK/(kind+'-baseline.3mf'));staged=b.read_zip(WORK/(kind+'-staged.3mf'))
    files=b.read_zip(WORK/(kind+'-slice/sliced.3mf'))
    result=json.loads((WORK/(kind+'-slice/result.json')).read_text())
    assert result['return_code']==0 and len(result['sliced_plates'])==COUNTS[kind]
    expected_settings=json.loads(staged['Metadata/project_settings.config']);settings=json.loads(files['Metadata/project_settings.config'])
    assert all(settings.get(k)==v for k,v in expected_settings.items()),{k:(v,settings.get(k)) for k,v in expected_settings.items() if settings.get(k)!=v}
    extras={k:v for k,v in settings.items() if k not in expected_settings}
    assert set(extras)<= {'different_settings_to_system','inherits_group','filament_map_2'},extras
    cfg=ET.fromstring(files['Metadata/model_settings.config']);scfg=ET.fromstring(staged['Metadata/model_settings.config'])
    oldcfg=ET.fromstring(reference['Metadata/model_settings.config'])
    info=ET.fromstring(files['Metadata/slice_info.config']);oldinfo=ET.fromstring(reference['Metadata/slice_info.config'])
    configs={b.props(o)['name'].split(' - ')[0]:o for o in cfg.findall('object')}
    sconfigs={b.props(o)['name'].split(' - ')[0]:o for o in scfg.findall('object')}
    root=ET.fromstring(files['3D/3dmodel.model']);sr=ET.fromstring(staged['3D/3dmodel.model']);oldroot=ET.fromstring(reference['3D/3dmodel.model'])
    assert len(root.find(b.tag('build')))==len(sr.find(b.tag('build')))==len(oldroot.find(b.tag('build')))
    assert set(configs)==set(sconfigs) and len(cfg.findall('plate'))==len(info.findall('plate'))==COUNTS[kind]
    modified={r['name']:r for r in stageinfo['objects']};checks=[];meshchecks=[]
    # All untouched object definitions and every build instance are byte-identical
    # before slicing. This includes the 32 copies of the small retainer.
    oldco={o.get('id'):o for o in oldcfg.findall('object')};sco={o.get('id'):o for o in scfg.findall('object')}
    oldresources={o.get('id'):o for o in oldroot.find(b.tag('resources'))}
    for oid,co in oldco.items():
        name=b.props(co)['name'].split(' - ')[0]
        if name in modified:continue
        assert b.xml(co)==b.xml(sco[oid])
        for c in oldresources[oid].find(b.tag('components')):
            path=c.get('{'+b.P+'}path').lstrip('/');assert reference[path]==staged[path]
        assert [b.xml(i) for i in oldroot.find(b.tag('build')) if i.get('objectid')==oid]==[b.xml(i) for i in sr.find(b.tag('build')) if i.get('objectid')==oid]
    # Check each instance, including repeated objects, survived native export.
    def instance_transforms(r,c):
        names={o.get('id'):b.props(o)['name'].split(' - ')[0] for o in c.findall('object')}
        groups={}
        for item in r.find(b.tag('build')):groups.setdefault(names[item.get('objectid')],[]).append(b.transform(item.get('transform')))
        return groups
    aa,ee=instance_transforms(root,cfg),instance_transforms(sr,scfg)
    for name in ee:
        assert len(aa[name])==len(ee[name])
        # Native export can recenter meshes; compare placement differences between
        # instances instead of assuming its component origins stay identical.
        a=b.np.array([t[:3,3] for t in aa[name]]);e=b.np.array([t[:3,3] for t in ee[name]])
        a-=a.mean(axis=0);e-=e.mean(axis=0)
        assert b.cKDTree(a).query(e)[0].max()<.0002,(name,'instances')
    _,outline,joints,_=b.layout()
    for plate in cfg.findall('plate'):
        n=int(b.props(plate)['plater_id']);names={next(k for k,co in configs.items() if co.get('id')==b.props(i)['object_id']) for i in plate.findall('model_instance')}
        actual=selected_entries(files,names);expected=selected_entries(staged,names)
        for name in names:
            assert len(actual[name])==len(expected[name])
            for k,v in b.props(sconfigs[name]).items():assert b.props(configs[name]).get(k)==v,(name,k)
            for a,e in zip(actual[name],expected[name]):
                error=max(b.cKDTree(a['mesh'].vertices).query(e['mesh'].vertices)[0].max(),b.cKDTree(e['mesh'].vertices).query(a['mesh'].vertices)[0].max())
                assert error<.0002,(kind,name,error)
                assert a['config'].get('subtype')==e['config'].get('subtype')
                for k,v in b.props(e['config']).items():
                    if k.startswith('source_') or k=='matrix':continue
                    # Native export drops redundant part assignments; the
                    # inherited object extruder must resolve to the same slot.
                    if k=='extruder':
                        assert b.props(a['config']).get(k,b.props(configs[name]).get(k))==v,(name,k)
                        continue
                    assert b.props(a['config']).get(k)==v,(name,k)
                for state in [4,8]:assert int((a['paint']==state).sum())==int((e['paint']==state).sum())
                meshchecks.append(dict(name=name,subtype=a['config'].get('subtype'),max_vertex_error_mm=float(error)))
        stat=next(p for p in info.findall('plate') if int(b.props(p)['index'])==n)
        prior=next(p for p in oldinfo.findall('plate') if int(b.props(p)['index'])==n)
        assert b.props(stat)['outside']=='false' and b.props(stat)['pause_count']=='0'
        assert {f.get('id') for f in stat.findall('filament')}=={f.get('id') for f in prior.findall('filament')}
        assert {o.get('identify_id') for o in stat.findall('object')}=={b.props(i)['identify_id'] for i in plate.findall('model_instance')}
        assert all(w.get('msg')=='not_support_traditional_timelapse' for w in stat.findall('warning'))
        b.setmeta(stat,'printer_model_id','N2S')
        first=float(b.props(stat).get('first_layer_time','0'))
        if not math.isfinite(first) or not 0<=first<=float(b.props(stat)['prediction']):stat.remove(stat.find("metadata[@key='first_layer_time']"))
        gcode=files[f'Metadata/plate_{n}.gcode'];text=gcode.decode()
        assert hashlib.md5(gcode).hexdigest().lower()==files[f'Metadata/plate_{n}.gcode.md5'].decode().strip().lower()
        assert not re.search(r'^\s*(?:M400\s+U1|M0(?:\s|$)|M1(?:\s|$)|M25(?:\s|$))',text,re.M)
        audit=b.scan_gcode(text);zs=audit.pop('model_extrusion_z_by_filament_mm');audit['model_z_ranges_mm']={k:[min(v),max(v)] for k,v in zs.items()}
        copper=[modified[name] for name in names if name in modified]
        if copper:assert audit['conservative_bed_edge_clearance_mm']>=1.5,(kind,n,audit['bead_xy_bounds_mm'])
        else:
            previous=b.scan_gcode(reference[f'Metadata/plate_{n}.gcode'].decode())
            assert audit['conservative_bed_edge_clearance_mm']>=max(0,previous['conservative_bed_edge_clearance_mm']-.05),(kind,n,audit['bead_xy_bounds_mm'])
            audit['previous_bed_edge_clearance_mm']=previous['conservative_bed_edge_clearance_mm']
        assert all(.1999<=min(v) and max(v)<250 for v in zs.values())
        motion=motion_audit(text)
        assert 'M201 X1000 Y1000 Z1500 E5000' in motion['axis_limit_commands']
        assert 'M203 X150 Y150 Z30 E30' in motion['axis_limit_commands']
        assert all(float(re.search(r'Y([\d.]+)',c)[1])<= (1000 if c.startswith('M201 ') else 150) for c in motion['axis_limit_commands'] if 'Y' in c)
        facechecks=[]
        if copper:
            assert motion['y_axis_upper_bounds']['extrusion_acceleration']<=1000.01,(kind,n,motion)
            assert motion['y_axis_upper_bounds']['travel_acceleration']<=1000.01,(kind,n,motion)
            assert motion['commanded_maxima']['extrusion_speed']<=150.01 and motion['commanded_maxima']['travel_speed']<=150.01,(kind,n,motion)
            assert set(zs)==({'3'} if kind=='normal' else {'1'})
            for f in ['Support','Support interface']:assert audit['features'].get(f,0)>0,(kind,n,f)
            if any(r['canonical'][0] in 'MT' for r in copper):assert audit['features'].get('Sparse infill',0)>0
            assert not audit['features'].get('Ironing',0) and not audit['features'].get('Prime tower',0)
            paths,volumes=b.support_paths(text);centers=paths['Support interface'].mean(axis=1)
            base=paths['Support'][b.np.max(paths['Support'][:,:,2],axis=1)<=.201]
            assert len(base)>0,(kind,n,'no tree base on bed')
            audit['tree_base_segment_count']=len(base)
            audit['tree_base_xy_bounds_mm']=[base[:,:,:2].min(axis=(0,1)).tolist(),base[:,:,:2].max(axis=(0,1)).tolist()]
            audit['brim_note']='6 mm outer object brim requested. Some tilted bodies have no printable first-layer area; their anchoring is the generated tree base, classified as Support instead of Brim.'
            for row in copper:
                name=row['name'];canonical=row['canonical'];body=actual[name][0]['mesh'].copy();body.apply_translation([*-plate_offset(n,6 if kind=='normal' else 3),0])
                t=b.np.array(row['build_transform']);near=b.np.all(centers>=body.bounds[0]-2,axis=1)&b.np.all(centers<=body.bounds[1]+2,axis=1)
                assert near.any(),(kind,name,'no support interface')
                local=b.trimesh.transform_points(centers[near],b.np.linalg.inv(t));body.apply_transform(b.np.linalg.inv(t))
                if canonical.startswith('B'):
                    j=joints[int(canonical[1:])-1];footprint=b.locate(b.rect(-6,-j[4],6,j[4]),j[2],j[3]).intersection(outline.buffer(-.15))
                else:footprint=b.mesh_slice(body,9)
                inside=b.shapely.contains(footprint.buffer(-.6),b.shapely.points(local[:,:2]));floor=10.5+b.crown(outline,local[inside,:2])-.6+.15
                delta=float((local[inside,2]-floor).max()) if inside.any() else None
                assert ((delta is not None and delta<.12) if canonical.startswith('B') else (delta is None or delta<-2)),(kind,name,delta)
                facechecks.append(dict(name=name,interface_points=int(near.sum()),interior_interface_points=int(inside.sum()),max_interface_above_band_underside_mm=delta))
        audit.update(plate=n,gcode_sha256=digest(gcode),weight_g=float(b.props(stat)['weight']),seconds=int(b.props(stat)['prediction']),motion=motion,support_face_checks=facechecks)
        checks.append(audit);print(kind,'verified plate',n,'clearance',round(audit['conservative_bed_edge_clearance_mm'],2),flush=True)
    files['Metadata/slice_info.config']=b.xml(info)
    ids=[]
    for path,data in files.items():
        if path.endswith('.model'):
            r=ET.fromstring(data);ids.extend(o.get('id') for o in r.find(b.tag('resources')))
            for c in r.iter(b.tag('component')):assert c.get('{'+b.P+'}path').lstrip('/') in files
    assert len(ids)==len(set(ids))
    for plate in cfg.findall('plate'):
        for k,v in b.props(plate).items():
            if k.endswith('_file') and v:assert v in files
    out=WORK/(kind+'-verified.3mf');b.write_zip(out,files)
    report=dict(project_sha256=b.sha(out),baseline_sha256=stageinfo['baseline_sha256'],plates=COUNTS[kind],objects=len(configs),instances=len(root.find(b.tag('build'))),
                changed_plates=checks,unchanged_native_plates=[],mesh_checks=meshchecks,orientation=stageinfo['objects'],choices=stageinfo['choices'],
                process_limits=TRAVEL,copper_overrides=COPPER,total_weight_g=sum(c['weight_g'] for c in checks),total_seconds=sum(c['seconds'] for c in checks),
                scope='Native slicing, unchanged geometry and digital support/motion checks. Full-height adhesion and sway still require a physical print.')
    (WORK/(kind+'-validation.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(kind,report['total_weight_g'],'g',report['total_seconds'],'seconds',flush=True)


def publish():
    for kind,path in SOURCES.items():
        report=json.loads((WORK/(kind+'-validation.json')).read_text());candidate=WORK/(kind+'-verified.3mf')
        assert b.sha(candidate)==report['project_sha256']
        targets=TARGETS if kind=='normal' else [path]
        for target in targets:assert b.sha(target) in [report['baseline_sha256'],report['project_sha256']]
    for kind,path in SOURCES.items():
        for target in (TARGETS if kind=='normal' else [path]):shutil.copy2(WORK/(kind+'-verified.3mf'),target)
        shutil.copy2(WORK/(kind+'-validation.json'),REVIEW/(kind+'-validation.json'))
    shutil.copy2(WORK/'normal-validation.json',PACKAGE/'y-stability-validation.json')
    print('Published corrected normal Dara, copper candidate, and band test.',flush=True)


def render(kind):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Line3DCollection
    files=b.read_zip(WORK/(kind+'-verified.3mf'));report=json.loads((WORK/(kind+'-validation.json')).read_text())
    plates=[1] if kind=='test' else (MPLATES[:6] if kind=='normal' else list(range(1,7)))
    fig=plt.figure(figsize=(11,7) if kind=='test' else (15,12),facecolor='#f4f1eb')
    for idx,n in enumerate(plates,1):
        ax=fig.add_subplot(1,1,1,projection='3d') if kind=='test' else fig.add_subplot(2,3,idx,projection='3d')
        ax.set_facecolor('#f4f1eb');plottext=files[f'Metadata/plate_{n}.gcode'].decode()
        # Group the exposed shell roles under the same plot color. This changes
        # only the plot input, never any saved toolpath or machine command.
        for role in ['Floating vertical shell','Overhang wall','Top surface']:
            plottext=plottext.replace('; FEATURE: '+role,'; FEATURE: Outer wall')
        paths,_=b.support_paths(plottext)
        for key,color,lw in [('Outer wall','#b76930',.35),('Support','#929ca5',.3),('Support interface','#277b83',.45)]:
            points=paths[key];points=points[::max(1,len(points)//22000)]
            ax.add_collection3d(Line3DCollection(points,colors=color,linewidths=lw,alpha=1 if key=='Outer wall' else .35))
        zmax=60 if kind=='test' else 256
        ax.set(xlim=(30,220) if kind=='test' else (0,256),ylim=(70,145) if kind=='test' else (0,256),zlim=(0,zmax))
        ax.set_box_aspect((190,75,zmax) if kind=='test' else (256,256,zmax))
        ax.quiver(215 if kind=='test' else 245,80 if kind=='test' else 30,1,0,55 if kind=='test' else 185,0,color='#175f88',linewidth=2,arrow_length_ratio=.08)
        ax.text(215 if kind=='test' else 245,110 if kind=='test' else 125,3,'Y bed travel',color='#175f88',fontsize=8)
        ax.set_xlabel('X (mm)');ax.set_ylabel('Y (mm)');ax.set_zlabel('Height (mm)');ax.view_init(25,35);ax.tick_params(labelsize=7)
        row=next(r for r in report['changed_plates'] if r['plate']==n)
        label='T2 + T3 + Band1' if kind=='test' else f'M{idx} / plate {n}'
        ax.set_title(f'{label} — {row["weight_g"]:.1f} g',fontsize=11)
    fig.suptitle('Y-aligned copper — actual Bambu toolpaths',fontsize=18)
    fig.text(.5,.025,'Face planes run along Y; faces lean across X at 55°. Copper: exposed shells · gray: trees · teal: interfaces\nTransparent paths sampled for clarity. Digital check; adhesion and sway at full height remain a physical test.',ha='center',fontsize=10)
    fig.tight_layout(rect=(0,.08,1,.94))
    if kind!='test':fig.subplots_adjust(hspace=.22)
    fig.savefig(REVIEW/(kind+'-supports.png'),dpi=140);plt.close(fig)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['stage','slice','motion','verify','publish','render']);ap.add_argument('kind',nargs='?',choices=list(SOURCES),default='normal');args=ap.parse_args()
    if args.action=='stage':stage()
    elif args.action=='slice':slice_project(args.kind)
    elif args.action=='verify':verify(args.kind)
    elif args.action=='publish':publish()
    elif args.action=='render':render(args.kind)
    else:
        f=b.read_zip(WORK/(args.kind+'-slice/sliced.3mf'))
        print(json.dumps({p:motion_audit(data.decode()) for p,data in f.items() if p.endswith('.gcode')},indent=2))
