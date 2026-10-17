"""Build negative, three-tile spray masks and a native six-plate A1 project."""
import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from build_jointed_bambu_project import ROOT, P, R, IDENTITY, model, tag, meta, uid, xml, mesh_object, np, trimesh
import manifold3d as mf
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch
from shapely.geometry import Polygon, box
from shapely.affinity import scale, translate, rotate
from shapely.ops import unary_union

OUT = ROOT / 'output/christmas-crate-stencils'
FONT = Path('C:/Windows/Fonts/STENCIL.TTF')

def lettering(text, width, height, x, y):
    contours = TextPath((0, 0), text, size=100, prop=FontProperties(fname=str(FONT))).to_polygons()
    shape = Polygon()
    for contour in contours:
        shape = shape.symmetric_difference(Polygon(contour))
    a,b,c,d = shape.bounds
    return translate(scale(translate(shape,-a,-b),xfact=width/(c-a),yfact=height/(d-b),origin=(0,0)),x,y)

def extrude(poly):
    contours = [np.asarray(poly.exterior.coords)[:-1]] + [np.asarray(r.coords)[:-1] for r in poly.interiors]
    solid = mf.CrossSection(contours, mf.FillRule.EvenOdd).extrude(.8).to_mesh()
    return trimesh.Trimesh(vertices=solid.vert_properties[:,:3],faces=solid.tri_verts,process=True)

def draw(ax, geom, color):
    for p in ([geom] if geom.geom_type == 'Polygon' else geom.geoms):
        ax.add_patch(Patch(np.asarray(p.exterior.coords), facecolor=color,edgecolor='none'))
        for ring in p.interiors:
            ax.add_patch(Patch(np.asarray(ring.coords),facecolor='#c99c68',edgecolor='none'))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    fragile = lettering('FRAGILE',660,105,30,27.5)
    top = lettering('THIS END UP',580,85,25,37.5)
    arrow = Polygon([(652,25),(674,25),(674,92),(700,92),(663,140),(626,92),(652,92)])
    masks = [('THIS-END-UP',unary_union([top,arrow])),('FRAGILE',fragile)]
    with zipfile.ZipFile(ROOT/'reference/tested-lap-joints/Tested-Joints-One-Plate.3mf') as z:
        preset=json.loads(z.read('Metadata/project_settings.config'))
        files={k:z.read(k) for k in ['[Content_Types].xml','_rels/.rels']}
    preset.update(print_settings_id='Crate stencil - 0.8mm - four solid layers',layer_height='0.2',initial_layer_print_height='0.2',wall_loops='2',top_shell_layers='4',bottom_shell_layers='4',sparse_infill_density='0%',sparse_infill_pattern='gyroid',enable_support='0',enable_prime_tower='0',brim_type='no_brim',print_sequence='by layer',ironing_type='no ironing')
    root=model(); del root.attrib['xmlns:p']
    for k,v in [('Application','BambuStudio-02.08.02.61'),('BambuStudio:3mfVersion','1'),('Title','Christmas crate negative spray stencils')]:
        ET.SubElement(root,tag('metadata'),name=k).text=v
    res=ET.SubElement(root,tag('resources')); build=ET.SubElement(root,tag('build'),attrib={'{'+P+'}UUID':uid()})
    config=ET.Element('config'); rels=ET.Element('Relationships',xmlns=R); records=[]
    fig,axes=plt.subplots(2,1,figsize=(14,7))
    for row,(label,holes) in enumerate(masks):
        sheet=box(0,0,720,160).difference(holes)
        assert sheet.geom_type=='Polygon', 'Loose letter centers'
        axes[row].set_facecolor('white'); draw(axes[row],sheet,'#75aac5')
        axes[row].set(xlim=(-10,730),ylim=(-10,180),aspect='equal',title=label+' — blue = plastic, tan = paint openings',xlabel='mm')
        for seam in (240,480): axes[row].axvline(seam,color='#d34c38',ls='--',lw=1)
        for col in range(3):
            i=row*3+col+1; name=f'{i:02d}-{label}-{col+1}-of-3'
            poly=sheet.intersection(box(col*240,0,(col+1)*240,160))
            assert poly.geom_type=='Polygon', (name,'Detached material at seam')
            mesh=extrude(translate(poly,-col*240,0))
            assert mesh.is_volume and len(mesh.split())==1
            assert np.allclose(mesh.extents,[240,160,.8])
            mesh.export(OUT/(name+'.stl'))
            oid=i*1000; path=f'3D/Objects/{name}.model'; child=model()
            mesh_object(ET.SubElement(child,tag('resources')),oid+1,mesh)
            obj=ET.SubElement(res,tag('object'),id=str(oid),type='model',attrib={'{'+P+'}UUID':uid()})
            ET.SubElement(ET.SubElement(obj,tag('components')),tag('component'),objectid=str(oid+1),transform=IDENTITY,attrib={'{'+P+'}path':'/'+path,'{'+P+'}UUID':uid()})
            files[path]=xml(child)
            ET.SubElement(rels,'Relationship',Target='/'+path,Id=f'rel-{i}',Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
            # Bambu lays six plates out in three columns and two rows.
            # Object coordinates must agree with the plate metadata, not just IDs.
            plate_origin = np.array([col*307.2, -row*307.2, 0])
            position = plate_origin + [8,48,0]
            ET.SubElement(build,tag('item'),objectid=str(oid),printable='1',transform=f'1 0 0 0 1 0 0 0 1 {position[0]} {position[1]} 0',attrib={'{'+P+'}UUID':uid()})
            conf=ET.SubElement(config,'object',id=str(oid)); meta(conf,'name',name); meta(conf,'extruder',1)
            part=ET.SubElement(conf,'part',id=str(oid+1),subtype='normal_part'); meta(part,'name',name)
            ET.SubElement(part,'mesh_stat',face_count=str(len(mesh.faces)),edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
            plate=ET.SubElement(config,'plate')
            for k,v in [('plater_id',i),('plater_name',name),('locked','false'),('filament_map_mode','Auto For Flush'),('filament_maps','1'),('filament_volume_maps','0')]: meta(plate,k,v)
            inst=ET.SubElement(plate,'model_instance')
            for k,v in [('object_id',oid),('instance_id',0),('identify_id',i)]:meta(inst,k,v)
            records.append(dict(plate=i,name=name,size_mm=mesh.extents.tolist(),watertight=bool(mesh.is_volume),connected_components=1,volume_mm3=mesh.volume))
        # Reassemble the tiles exactly; the split must not change any paint opening.
        rebuilt=unary_union([sheet.intersection(box(c*240,0,(c+1)*240,160)) for c in range(3)])
        assert rebuilt.symmetric_difference(sheet).area < 1e-7
    fig.tight_layout(); fig.savefig(OUT/'mask-layout.png',dpi=150); plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,8)); ax.set_facecolor('#c99c68')
    draw(ax,translate(top.union(arrow),249.6,880),'#202020')
    draw(ax,translate(rotate(fragile,20,origin=(360,80)),249.6,480),'#202020')
    ax.set(xlim=(0,1219.2),ylim=(0,1219.2),aspect='equal',title='Suggested layout on a 4 ft × 4 ft crate',xlabel='mm',ylabel='mm')
    fig.savefig(OUT/'crate-preview.png',dpi=150,bbox_inches='tight'); plt.close(fig)
    files.update({'3D/3dmodel.model':xml(root),'3D/_rels/3dmodel.model.rels':xml(rels),'Metadata/model_settings.config':xml(config),'Metadata/project_settings.config':json.dumps(preset,indent=2).encode()})
    with zipfile.ZipFile(OUT/'Christmas-Crate-Stencils.3mf','w',zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items():z.writestr(name,data)
    with zipfile.ZipFile(OUT/'Christmas-Crate-Stencils.3mf') as z:
        assert z.testzip() is None
        for name in z.namelist():
            if name.endswith(('.xml','.model','.rels','model_settings.config')):
                ET.fromstring(z.read(name))
        assert len(ET.fromstring(z.read('Metadata/model_settings.config')).findall('plate'))==6
        saved_settings = json.loads(z.read('Metadata/project_settings.config'))
        assert saved_settings['printer_model']=='Bambu Lab A1'
        assert saved_settings['sparse_infill_pattern']=='gyroid'
        assert saved_settings['sparse_infill_density']=='0%'
        assert int(saved_settings['bottom_shell_layers']) >= 4
        assert int(saved_settings['top_shell_layers']) >= 4
        assert float(saved_settings['layer_height']) == .2
        assert float(saved_settings['initial_layer_print_height']) == .2
        # Validate serialized transforms against the actual six-plate bed grid.
        saved_root = ET.fromstring(z.read('3D/3dmodel.model'))
        saved_config = ET.fromstring(z.read('Metadata/model_settings.config'))
        items = {int(item.get('objectid')): item for item in saved_root.find(tag('build'))}
        for index, plate in enumerate(saved_config.findall('plate')):
            instance = plate.find('model_instance')
            oid = int(instance.find("metadata[@key='object_id']").get('value'))
            offset = np.array(list(map(float,items[oid].get('transform').split()))[-3:])
            origin = np.array([(index%3)*307.2,-(index//3)*307.2,0])
            local = offset-origin
            assert np.allclose(local,[8,48,0]), (index+1,local)
            assert np.all(local[:2]>=8) and np.all(local[:2]+[240,160]<=248)
    (OUT/'validation.json').write_text(json.dumps(records,indent=2))
    print(json.dumps(records,indent=2))

if __name__=='__main__':main()
