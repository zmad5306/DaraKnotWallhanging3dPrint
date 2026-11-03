import sys,json,math
from pathlib import Path
# Requires numpy and trimesh installed in your Python environment.
import trimesh,numpy as np
p=Path(__file__).resolve().parents[1];d=json.loads((p/'project-data.json').read_text());cad=p/'CAD';cad.mkdir(exist_ok=True)
parts={r['part']:r for r in d['parts']};scene=trimesh.Scene()
scad=['// v32 synchronized CAD review assembly. Units: mm. Mesh-based exact printable geometry.',
'// Keep this file inside CAD/ next to the package STL/ folder.',
'// Toggle components or explode the letter for inspection. F5 previews the model.',
'show_knot = true; show_letter = true; show_mount_dowels = true;',
'mounting = "screws"; // [screws,adhesive,none]',
'letter_lift = 0; // Set to 100 to inspect the rear of the M.',
'$vpt=[0,0,0]; $vpr=[0,0,0]; $vpd=1800;']
def add(name,part,transform=None,cond='true',color=[.87,.89,.87]):
 r=parts[part];assembly=np.array(r['assembly_transform']);tf=np.eye(4) if transform is None else transform
 combined=tf@assembly
 t=trimesh.load_mesh(p/r['file'],process=False);t.apply_transform(combined);t.visual.vertex_colors=np.array([int(x*255) for x in color]+[255],dtype=np.uint8)
 scene.add_geometry(t,geom_name=name,node_name=name)
 scad.append(f'// {name}\nif ({cond}) color({json.dumps(color)}) multmatrix({json.dumps(combined.tolist())}) import("../{r["file"]}");')
for r in d['parts']:
 if '/knot/' in r['file']:add(r['part'],r['part'],cond='show_knot')
 if '/letter/' in r['file']:
  before=len(scad);add(r['part'],r['part'],cond='show_letter',color=[.97,.95,.90]);scad[-1]=scad[-1].replace('color(', 'translate([0,0,letter_lift]) color(')
def pose(x,y,z,angle=0):
 tf=trimesh.transformations.rotation_matrix(math.radians(angle),[0,0,1]);tf[:3,3]=[x,y,z];return tf
for j in d['joints']:add(j['id'],'SPLICE_50x18' if j['length']==50 else 'SPLICE_30x12',pose(j['x'],j['y'],.2,j['angle']),cond='show_mount_dowels',color=[.65,.72,.74])
for j in d['M_joints']:add(j['id'],'M_SPLICE_30x8',pose(j['x'],j['y'],18.2,j['angle']),cond='show_mount_dowels',color=[.65,.72,.74])
for i,q in enumerate(d['letter_mounts']):add('A'+str(i+1),'M_LOCATING_DOWEL',pose(q['x'],q['y'],16.6),cond='show_mount_dowels',color=[.65,.72,.74])
for q in d['wall_mounts']:add(q['id'],'WALL_KEYHOLE_BLOCK',pose(q['x'],q['y'],-10),cond='mounting == "screws"',color=[.65,.72,.74])
for q in d['adhesive_pad_sites']:
 r=parts['OPTIONAL_ADHESIVE_PAD_110x30'];combined=pose(q['x'],q['y'],-10,q['angle'])@np.array(r['assembly_transform'])
 scad.append(f'if (mounting == "adhesive") color([.65,.72,.74]) multmatrix({json.dumps(combined.tolist())}) import("../{r["file"]}");')
(cad/'Dara-Review-Assembly.scad').write_text('\n'.join(scad),encoding='utf-8')
import zipfile,xml.etree.ElementTree as ET
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('',ns)
root=ET.Element('{'+ns+'}model',{'unit':'millimeter'});resources=ET.SubElement(root,'resources');ids=[]
for i,(name,t) in enumerate(scene.geometry.items(),1):
 obj=ET.SubElement(resources,'object',{'id':str(i),'type':'model','name':name});mesh=ET.SubElement(obj,'mesh');vs=ET.SubElement(mesh,'vertices');ts=ET.SubElement(mesh,'triangles')
 for x,y,z in t.vertices:ET.SubElement(vs,'vertex',{'x':f'{x:.6f}','y':f'{y:.6f}','z':f'{z:.6f}'})
 for a,b,cc in t.faces:ET.SubElement(ts,'triangle',{'v1':str(a),'v2':str(b),'v3':str(cc)})
 ids.append(i)
assembly=ET.SubElement(resources,'object',{'id':str(len(ids)+1),'type':'model','name':'Dara synchronized FULL SIZE REVIEW ONLY'});components=ET.SubElement(assembly,'components')
for i in ids:ET.SubElement(components,'component',{'objectid':str(i)})
build=ET.SubElement(root,'build');ET.SubElement(build,'item',{'objectid':str(len(ids)+1)})
with zipfile.ZipFile(cad/'Dara-Review-Assembly.3mf','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
 z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
 z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
scene.export(cad/'Dara-Review-Assembly.glb')
(cad/'READ-ME.txt').write_text('CAD REVIEW - NOT A PRINT PLATE\n\nOpen Dara-Review-Assembly.scad in OpenSCAD for component toggles and an exploded M view. This is an exact mesh-based CAD assembly, not a feature-based STEP model. Keep the extracted package folder intact: it imports the adjacent STL files.\n\nDara-Review-Assembly.3mf is the complete full-size assembled artwork, including integral locating joints and screw wall blocks. Use it ONLY for review; do not scale it to fit a bed or print it as one object. Grouped print projects are in Bambu-Studio/Grouped-Projects/. Repairs synchronized on October 10, 2026. Existing completed parts remain compatible.\n\nDara-Review-Assembly.glb is an alternative 3D viewing file.\n\nThe printable STLs are the authoritative current geometry. Historical generators in source/ predate these repairs; use export_current_cad.py to regenerate this mesh-based CAD review from the current STLs. Units throughout are millimetres.\n',encoding='utf-8')
print('CAD exported:',len(scene.geometry),'assembled bodies')
