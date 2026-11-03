"""Controlled digital checks of mesh sampling, matched skins and simplification."""
import sys,json,subprocess,copy,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'.work/python-libs')]
import prepare_hammered_bands as b
from prepare_cover_crown_test import shape
from prepare_cover_precision_test import face_paths
W=ROOT/'.work/cover-tessellation';W.mkdir(exist_ok=True)
LABELS=['baseline','tight-slicing','fine-mesh','matched-skins','no-inner-plateau']
T=b.np.array(json.loads((ROOT/'.work/cover-crown/stage.json').read_text())['orientation']['build_transform'])

def matched_skin(upper,floor):
    # Preserve the closed envelope's topology; remap its flat underside.
    body=upper.copy();v=body.vertices.copy();mask=abs(v[:,2]-6.6)<1e-8
    assert mask.any()
    v[mask,2]=floor(v[mask,:2]);body.vertices=v
    return body

def stage(label,body,resolution):
    assert body.is_volume and body.is_watertight and body.body_count==1
    files=b.read_zip(ROOT/'.work/cover-crown/staged.3mf')
    child=b.model();cr=ET.SubElement(child,b.tag('resources'));b.mesh_object(cr,1001,body)
    tri=cr.find(b.tag('object')).find(b.tag('mesh')).find(b.tag('triangles'))
    normal=body.face_normals@T[:3,:3].T;front=body.face_normals[:,2]>-.01
    for i in b.np.where(front|(normal[:,2]<-.1))[0]:
        tri[i].set('paint_supports','8' if front[i] else '4')
    files['3D/Objects/B1.model']=b.xml(child)
    settings=json.loads(files['Metadata/project_settings.config']);settings['resolution']=resolution
    settings['print_settings_id']='DIGITAL CHECK '+label
    assert settings['wall_generator']=='classic' and settings['enable_arc_fitting']=='0'
    files['Metadata/project_settings.config']=json.dumps(settings,indent=2).encode()
    cfg=ET.fromstring(files['Metadata/model_settings.config'])
    b.setmeta(cfg.find('object'),'name','B1 - DIGITAL CHECK '+label)
    b.setmeta(cfg.find('plate'),'plater_name','DIGITAL CHECK '+label)
    stat=cfg.find('object').find('part').find('mesh_stat');stat.set('face_count',str(len(body.faces)))
    files['Metadata/model_settings.config']=b.xml(cfg)
    b.write_zip(W/(label+'.3mf'),files)
    b.np.savez_compressed(W/(label+'.npz'),vertices=body.vertices,faces=body.faces)
    print(label,len(body.faces),'triangles',float(body.volume),'mm3',flush=True)

def geometry():
    region,floor,top=shape(1)
    old=b.np.load(ROOT/'.work/cover-crown/B1.npz');baseline=b.trimesh.Trimesh(old['vertices'],old['faces'],process=False)
    stage('baseline',baseline,'0.001');stage('tight-slicing',baseline,'0.0001')
    upper=b.band_envelope(region,top,res=.125,tolerance=.00025)
    fine=b.boolean([upper,b.envelope(floor,region.bounds,.125)],'difference')
    stage('fine-mesh',fine,'0.001')
    matched=matched_skin(upper,floor);stage('matched-skins',matched,'0.001')
    # All variants retain the same analytical shape functions and print pose.
    report={}
    for label,body in [('baseline',baseline),('fine-mesh',fine),('matched-skins',matched)]:
        rows=[]
        for sign,evaluate in [(1,top),(-1,floor)]:
            tri=body.triangles[sign*body.face_normals[:,2]>.01]
            p=b.np.concatenate([tri.mean(axis=1)[:,None,:],(tri+b.np.roll(tri,-1,axis=1))/2],axis=1).reshape(-1,3)
            e=b.np.abs(p[:,2]-evaluate(p[:,:2]));rows.append({'max_mm':float(e.max()),'p99_mm':float(b.np.percentile(e,99))})
        interior=body.triangles_center[body.face_normals[:,2]>.01,:2]
        thick=top(interior)-floor(interior)
        report[label]={'triangles':len(body.faces),'top_error':rows[0],'underside_error':rows[1],
                       'vertical_thickness_range_mm':[float(thick.min()),float(thick.max())]}
    (W/'geometry.json').write_text(json.dumps(report,indent=2))

def slice_all():
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    for label in LABELS:
        out=W/label;out.mkdir(exist_ok=True)
        with (out/'cli.log').open('w') as log:
            p=subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf','--outputdir',str(out),str(W/(label+'.3mf'))],
                             cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        print(label,p.returncode,flush=True);assert p.returncode==0

def analyze():
    result={}
    for label in LABELS:
        text=(W/label/'plate_1.gcode').read_text();paths,stats=face_paths(text,T)
        (W/(label+'-joins.json')).write_text(json.dumps(stats,indent=2))
        stats.pop('joins');result[label]=stats
    (W/'toolpaths.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':
    {'geometry':geometry,'slice':slice_all,'analyze':analyze}[sys.argv[1]]()

