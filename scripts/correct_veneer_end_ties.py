"""Move the two r5 bed bands to the open ends; preserve all other production stock.

This migration starts from the published r5 project, not a regenerated design.
The user's correction changes only the locations of the 4 x 0.6 mm bands.
"""
import argparse,copy,json,shutil,subprocess
import promote_veneer_wall_cradle as p
from promote_veneer_wall_cradle import np,ET,tag,props,xml,sha,save_json,ROOT,OUT
from development_3mf import solid,mesh,mesh_xml
import manifold3d as mf
import trimesh

WORK=ROOT/'.work/veneer-end-ties-r6'
EXPECTED='80bfee7600cf2cf3ba7252bb733bf203486639e94461158c9200c5f9f0f550a7'
REVISION='wall-cradle-r6-end-ties'

def configure(module=p):
    for k,v in dict(WORK=WORK,BASE=WORK/'baseline',NATIVE=WORK/'native',
        EDIT=WORK/'wall-cradle-editable.3mf',EXPECTED_SOURCE=EXPECTED,REVISION=REVISION).items():setattr(module,k,v)

configure()

def block(x,y,z,at):return mf.Manifold.cube([x,y,z]).translate(at)

def geometry():
    files=p.read(p.BASE/'Dara.3mf')
    original=json.loads((p.BASE/OUT.relative_to(ROOT)/'M-geometry-validation.json').read_text())
    for i,skin in enumerate(original['skins'],1):
        _,_,source_object,_,_,old,t=p.selected(files,i+14)
        v=p.vertices(old)@t[:3,:3].T+t[:3,3]
        f=np.array([[int(q.get(k)) for k in ('v1','v2','v3')] for q in old.find(tag('triangles'))])
        source=trimesh.Trimesh(v,f,process=False);body=solid(source)
        c=copy.deepcopy(skin['carrier']);pose=np.array(skin['assembly_to_printer'])
        oldbands=c['bed_tie_bands'];xmin,xmax=oldbands[0]['x_span_mm']
        # Analytic masks of the EXISTING walls and original bonded necks.
        # Subtract only band wings, leaving the interior web feet intact.
        rear_x=min(q[0] for q in c['webs'][0]['xz_profile'])
        masks=[block(2000,2000,c['support_panel_thickness_mm'],[-1000,-1000,
            c['backing_panel_top_assembly_z_mm']-c['support_panel_thickness_mm']]).transform(pose[:3]),
            block(c['rear_wall_thickness_mm'],320,325,[rear_x,0,0])]
        masks += [block(330,c['web_thickness_mm'],325,[0,w['y_mm']-c['web_thickness_mm']/2,0]) for w in c['webs']]
        inverse=np.linalg.inv(pose)
        for probe in c['bond_probes_print_xyz_mm']:
            q=inverse[:3,:3]@np.asarray(probe)+inverse[:3,3]
            masks.append(block(1.2002,1.2002,4.9002,[q[0]-.6001,q[1]-.6001,4.2999]).transform(pose[:3]))
        protected=mf.Manifold.batch_boolean(masks,mf.OpType.Add)
        oldmask=mf.Manifold.batch_boolean([block(b['x_span_mm'][1]-b['x_span_mm'][0]+2e-6,b['width_mm']+2e-6,b['height_mm']+1e-6,
            [b['x_span_mm'][0]-1e-6,b['center_y_mm']-b['width_mm']/2-1e-6,-1e-7]) for b in oldbands],mf.OpType.Add)
        base_vertices=v[np.abs(v[:,2])<1e-6]
        ymin,ymax=map(float,[base_vertices[:,1].min(),base_vertices[:,1].max()])
        bands=[dict(x_span_mm=[xmin,xmax],center_y_mm=y,width_mm=4.,height_mm=.6,
            location=label,outer_edge_y_mm=edge) for y,label,edge in [(ymin+2,'minimum-Y open end',ymin),(ymax-2,'maximum-Y open end',ymax)]]
        newmask=mf.Manifold.batch_boolean([block(xmax-xmin,4,.6,[xmin,b['center_y_mm']-2,0]) for b in bands],mf.OpType.Add)
        candidate=(body-(oldmask-protected))+newmask
        assert candidate.status()==mf.Error.NoError
        pieces=[x for x in candidate.decompose() if abs(x.volume())>1e-7]
        assert len(pieces)==1
        candidate=pieces[0];cm=mesh(candidate)
        removed=body-candidate;added=candidate-body
        above=block(330,320,325,[0,0,.600002])
        outside=abs(((removed+added)-oldmask-newmask).volume())
        above_difference=abs((removed^above).volume())+abs((added^above).volume())
        protected_removed=abs((removed^protected).volume())
        assert outside<1e-4 and above_difference<1e-4 and protected_removed<1e-4,(outside,above_difference,protected_removed)
        end_contacts=[]
        for b in bands:
            band=block(xmax-xmin,4,.6,[xmin,b['center_y_mm']-2,0])
            contacts=[float((band^body^m).volume()) for m in masks[:2]]
            assert min(contacts)>1.,contacts
            end_contacts.append(dict(location=b['location'],front_and_rear_overlap_mm3=contacts))
        np.savez_compressed(WORK/f'V{i}-candidate.npz',vertices=cm.vertices,faces=cm.faces)
        cm.export(WORK/f'V{i}-candidate.ply')
        source.export(WORK/f'V{i}-source.ply')
        density=float(json.loads(files['Metadata/project_settings.config'])['filament_density'][2])
        c.update(revision=REVISION,source_sha256=EXPECTED,source_name=props(source_object)['name'],source_object_id=source_object.get('id'),
            source_volume_mm3=body.volume(),candidate_volume_mm3=candidate.volume(),
            source_modeled_material_g_at_saved_density=body.volume()*density/1000,
            inherited_wall_geometry_validation='veneer-wall-r5-promotion-validation.json',
            bed_tie_bands=bands,previous_bed_tie_bands=oldbands,band_location='two open ends, flush outer edges',
            end_wall_contacts=end_contacts,source_wall_y_extent_mm=[ymin,ymax],
            removed_interior_band_volume_mm3=removed.volume(),added_end_band_volume_mm3=added.volume(),
            difference_outside_band_masks_mm3=outside,difference_above_band_height_mm3=above_difference,
            protected_wall_and_neck_removed_mm3=protected_removed,connected_components=1,
            minimum_bounds_mm=cm.bounds[0].tolist(),maximum_bounds_mm=cm.bounds[1].tolist(),
            modeled_material_g_at_saved_density=candidate.volume()*density/1000,
            physical_confirmation_pending=True)
        save_json(WORK/f'V{i}-geometry.json',c)
        print(f'V{i}: end bands Y={bands[0]["center_y_mm"]:.3f}, {bands[1]["center_y_mm"]:.3f}; wall/neck loss {protected_removed:.8f} mm3',flush=True)

def patch(source,target):
    original=p.read(source);files=dict(original);changed=[];paint=[]
    for i in range(1,4):
        cfg,plate,obj,path,child,old,t=p.selected(files,i+14)
        data=np.load(WORK/f'V{i}-candidate.npz');cm=trimesh.Trimesh(data['vertices'],data['faces'],process=False)
        pose=np.array(json.loads((WORK/f'V{i}-geometry.json').read_text())['assembly_to_printer'])
        # This is the same normal-based painting rule used in r5. Verify its
        # equivalence to the saved source triangle attributes before using it.
        ov=p.vertices(old)@t[:3,:3].T+t[:3,3]
        ot=list(old.find(tag('triangles')))
        of=np.array([[int(q.get(k)) for k in ('v1','v2','v3')] for q in ot])
        om=trimesh.Trimesh(ov,of,process=False)
        expected=om.face_normals@pose[:3,2]>.01
        actual=np.array([q.get('paint_supports')=='8' for q in ot])
        # Serialization can change the normal of sub-micron sliver triangles.
        # Require exact agreement on every meaningful source face and carry
        # saved attributes over to matching triangles, including those slivers.
        mismatch_area=float(om.area_faces[actual!=expected].sum())
        assert mismatch_area<1e-6,('Source paint rule mismatch area',mismatch_area)
        resources=ET.Element(tag('resources'));mesh_xml(resources,1,cm,True,pose[:3,2])
        replacement=resources[0].find(tag('mesh'))
        distances,indices=p.cKDTree(om.triangles_center).query(cm.triangles_center)
        copied=0
        for face,distance,index in zip(replacement.find(tag('triangles')),distances,indices):
            if distance<1e-6:
                face.attrib.pop('paint_supports',None)
                if ot[index].get('paint_supports') is not None:face.set('paint_supports',ot[index].get('paint_supports'))
                copied+=1
        inverse=np.linalg.inv(t)
        local=cm.vertices@inverse[:3,:3].T+inverse[:3,3]
        for vertex,point in zip(replacement.find(tag('vertices')),local):
            for key,value in zip(('x','y','z'),point):vertex.set(key,format(float(value),'.12g'))
        parent=next(o for o in child.find(tag('resources')) if o.find(tag('mesh')) is old)
        parent.remove(old);parent.append(replacement);files[path]=xml(child);changed.append(path)
        name=f'V{i} A2L hammered veneer and wall cradle r6 end ties'
        p.setmeta(obj,'name',name);p.setmeta(obj.find('part'),'name',name)
        count=str(len(cm.faces));obj.find('part/mesh_stat').set('face_count',count)
        for meta in obj.findall('metadata'):
            if 'face_count' in meta.attrib:meta.set('face_count',count)
        p.setmeta(plate,'plater_name',f'{i+14} - {name}')
        files['Metadata/model_settings.config']=xml(cfg)
        paint.append(dict(veneer=i,saved_support_paint_rule_verified=True,
            serialization_sliver_mismatch_area_mm2=mismatch_area,matching_face_attributes_copied=copied))
    assert all(files[n]==v for n,v in original.items() if n not in set(changed)|{'Metadata/model_settings.config'})
    p.write(target,files)
    return dict(source_sha256=sha(source),target_sha256=sha(target),changed_child_assets=changed,
        saved_transforms_and_global_settings_byte_preserved=True,support_painting=paint)

def build():
    save_json(WORK/'geometry-patch.json',dict(revision=REVISION,
        editable=patch(p.BASE/OUT.relative_to(ROOT)/'Dara-A2L-Editable.3mf',p.EDIT),
        native=patch(p.BASE/'Dara.3mf',WORK/'wall-cradle-native.3mf')))

def preview():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    fig,axes=plt.subplots(1,3,figsize=(13,5),facecolor='white')
    for i,ax in enumerate(axes,1):
        data=np.load(WORK/f'V{i}-candidate.npz');m=solid(trimesh.Trimesh(data['vertices'],data['faces'],process=False))
        c=json.loads((WORK/f'V{i}-geometry.json').read_text())
        def area(loop):return np.sum(loop[:,0]*np.roll(loop[:,1],-1)-loop[:,1]*np.roll(loop[:,0],-1))/2
        for loop in sorted(m.slice(.1).to_polygons(),key=lambda loop:-abs(area(loop))):
            ax.fill(loop[:,0],loop[:,1],color='#9a6b39' if area(loop)>0 else 'white',edgecolor='none')
        for b in c['bed_tie_bands']:
            ax.add_patch(plt.Rectangle((b['x_span_mm'][0],b['center_y_mm']-2),np.diff(b['x_span_mm'])[0],4,color='#ee514d'))
        ax.set(xlim=(40,280),ylim=(20,300),aspect='equal',title=f'V{i} / plate {i+14}',xlabel='Bed X (mm)')
        ax.grid(alpha=.15)
    axes[0].set_ylabel('Bed Y (mm)')
    fig.suptitle('Corrected bed contact: two thin ties at the open ends (red)',fontsize=15)
    fig.tight_layout();fig.savefig(WORK/'end-tie-bed-preview.png',dpi=150);plt.close(fig)

def reopen():
    folder=WORK/'reopen';folder.mkdir(exist_ok=True)
    save_json(folder/'input.json',dict(project_sha256=sha(p.NATIVE/'sliced.3mf')))
    for attempt in range(4):
        with (folder/'cli.log').open('w') as log:
            r=subprocess.run([str(p.EXE),'--info','--outputdir',str(folder),str(p.NATIVE/'sliced.3mf')],
                cwd=p.EXE.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        if r.returncode!=3221225477:break
    r.check_returncode()
    assert json.loads((folder/'result.json').read_text())['return_code']==0

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['snapshot','geometry','build','preview','slice','merge','reopen','validate','install','release']);a=parser.parse_args()
    if a.action=='slice':
        for number in [15,16,17]:p.slice_plate(number)
    elif a.action in ['snapshot','merge']:getattr(p,a.action)()
    elif a.action=='validate':
        import validate_veneer_wall_promotion as v
        configure(v);v.CORRECTION_GEOMETRY=WORK;v.run()
    elif a.action in ['install','release']:
        import install_veneer_wall_cradle as install
        configure(install);install.CORRECTION_GEOMETRY=WORK;getattr(install,a.action)()
    else:globals()[a.action]()
