from pathlib import Path
import sys,json
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
import trimesh,numpy as np
p=Path('working/Dara-Photo-Frame-A1-Jointed.scad');s=p.read_text()
d=json.loads(Path('.work/jointed-data.json').read_text())
s=s.replace('show_section_ids = false;','fast_preview = true; // Exact embedded default-shape preview; F6 always evaluates the CAD.\nshow_section_ids = false;')
s=s.replace('module section_shape(kind,i) {','''// OpenSCAD 2021's 32-bit CGAL cache can fail when all complex sections are
// evaluated together in F5. The self-contained preview below uses the checked
// section tessellations; all native CSG construction remains editable above.
// Changing a body parameter automatically falls back to the native CSG preview.
// F6, section export and geometry checks always use the native construction.
function cached_shape_matches() = fabric_style=="woven" && fabric_pitch==8 &&
    fabric_thread_width==2 && backer_thickness==1.6 && photo_allowance==.4 &&
    rabbet_overlap==4;
module section_shape(kind,i) {
    if($preview && fast_preview && cached_shape_matches()) preview_section(kind,i);
    else section_csg(kind,i);
}
module section_csg(kind,i) {''')
chunks=['\n// DEFAULT-GEOMETRY PREVIEW CACHE. No external mesh files are required.\n']
for family,info in d.items():
    for i,pl in enumerate(info['placements']):
        m=trimesh.load_mesh(f'.work/jointed-{family[0].upper()}{i+1}.stl')
        assert m.is_watertight and len(m.split())==1
        zshift=3.2 if family=='frame' and m.extents[2]>15 else 0
        m.apply_translation([*pl['centre'],-zshift])
        m.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(-pl['angle']),[0,0,1]))
        coords=np.round(m.vertices,7).tolist();faces=m.faces[:,::-1].tolist()
        chunks.append(f'module preview_{family}_{i}() {{\n polyhedron(points=')
        chunks.append(json.dumps(coords,separators=(',',':')))
        chunks.append(',\n faces='+json.dumps(faces,separators=(',',':'))+',convexity=50);\n}\n')
chunks.append('module preview_section(kind,i) {\n')
for family,info in d.items():
    for i in range(len(info['placements'])):chunks.append(f' if(kind=="{family}" && i=={i}) preview_{family}_{i}();\n')
chunks.append('}\n')
s+=''.join(chunks)
# Update inherited prose only in the new copy.
s=s.replace('// M is a separate solid part: use view_mode="M" to place its bottom at Z=0.','// M is a separate sectioned assembly: view_mode="M" puts its bottom at Z=0.')
s=s.replace('// Keep the original backers/retainers and M-to-frame attachment as in the source.','// Original backers/retainers are preserved; M-to-frame mounting is outside this change.')
p.write_text(s)
print('CAD bytes',p.stat().st_size)
