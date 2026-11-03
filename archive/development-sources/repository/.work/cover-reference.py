"""Digital controls only: same slicer settings, independent simple geometry."""
import sys,json,copy,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
sys.path[:0]=['scripts','.work/python-libs']
import prepare_hammered_bands as b

W=b.ROOT/'.work/cover-reference';W.mkdir(exist_ok=True)
base=b.read_zip(b.ROOT/'Dara-Cover-Smooth-Crown-Test.3mf')
j=b.layout()[2][0]
rot=b.np.array(json.loads((b.ROOT/'.work/cover-crown/stage.json').read_text())['orientation']['build_transform'])@b.rotation(j[3])
rot[:3,3]=0

def cylinder_strip():
    y=b.np.linspace(-20,20,161)
    radius=(20**2+2.2**2)/(2*2.2)
    z=1.2+b.np.sqrt(radius**2-y**2)-b.np.sqrt(radius**2-20**2)
    section=b.np.vstack([b.np.column_stack([y,z]),b.np.column_stack([y[::-1],z[::-1]-1.2])])
    n=len(section);v=b.np.vstack([b.np.column_stack([b.np.full(n,x),section]) for x in [-6,6]])
    f=[]
    for k in range(n):
        q=(k+1)%n;f.extend([[k,q,n+q],[k,n+q,n+k]])
    # Direct top/bottom pairs form the two end caps; no Boolean or triangulator.
    for i in range(len(y)-1):
        a,c=i,i+1;d,e=n-1-i,n-2-i
        f.extend([[a,c,e],[a,e,d],[n+a,n+e,n+c],[n+a,n+d,n+e]])
    m=b.trimesh.Trimesh(v,f,process=True);m.fix_normals()
    assert m.is_volume and m.is_watertight and m.body_count==1
    return m

def stage(label,body):
    source=base
    settings=json.loads(source['Metadata/project_settings.config'])
    settings['print_settings_id']='Digital geometry control - '+label
    files={k:source[k] for k in ['[Content_Types].xml','_rels/.rels']}
    root=b.model();del root.attrib['xmlns:p']
    for k,v in [('Application','BambuStudio-02.08.02.61'),('BambuStudio:3mfVersion','1'),('Title','Digital control '+label)]:
        ET.SubElement(root,b.tag('metadata'),name=k).text=v
    resources=ET.SubElement(root,b.tag('resources'));build=ET.SubElement(root,b.tag('build'),attrib={'{'+b.P+'}UUID':b.uid()})
    config=ET.Element('config');relations=ET.Element('Relationships',xmlns=b.R)
    t=b.centered(body,rot,[128,128])
    row=b.add_object(files,resources,build,config,relations,'B-reference',body,t,1000,[],[])
    original=ET.fromstring(source['Metadata/model_settings.config']).find('object')
    cfg=config.find('object')
    for node in list(cfg.findall('metadata')):cfg.remove(node)
    for key,value in b.props(original).items():
        if key is not None:b.meta(cfg,key,value)
    b.setmeta(cfg,'name','DIGITAL CONTROL '+label)
    plate=ET.SubElement(config,'plate')
    for key,value in [('plater_id',1),('plater_name','DIGITAL CONTROL '+label),('locked','false'),('filament_map_mode','Auto For Flush'),('filament_maps','1 1 1 1'),('filament_volume_maps','0 0 0 0')]:b.meta(plate,key,value)
    inst=ET.SubElement(plate,'model_instance')
    for key,value in [('object_id',1000),('instance_id',0),('identify_id',1)]:b.meta(inst,key,value)
    files.update({'3D/3dmodel.model':b.xml(root),'3D/_rels/3dmodel.model.rels':b.xml(relations),
        'Metadata/model_settings.config':b.xml(config),'Metadata/project_settings.config':json.dumps(settings,indent=2).encode()})
    b.write_zip(W/(label+'.3mf'),files)
    (W/(label+'.json')).write_text(json.dumps(row,indent=2))
    print(label,'staged',len(body.faces),flush=True)

if __name__=='__main__':
    if sys.argv[1]=='stage':
        flat=b.trimesh.creation.box(extents=[12,40,1.2]);flat.apply_translation([0,0,.6])
        stage('flat',flat);stage('cylinder',cylinder_strip())
    elif sys.argv[1]=='slice':
        for label in ['flat','cylinder']:
            out=W/label;out.mkdir(exist_ok=True)
            exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
            with (out/'cli.log').open('w') as log:
                run=subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf','--outputdir',str(out),str(W/(label+'.3mf'))],cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            print(label,run.returncode,flush=True)
            assert run.returncode==0
