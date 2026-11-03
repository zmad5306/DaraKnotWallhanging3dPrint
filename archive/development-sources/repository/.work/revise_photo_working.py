exec(open(".work/create_photo_working.py").read().split("header=s.split")[0])
s=s.replace('\r\n','\n')
header=s.split('// FROZEN ARTWORK OUTLINES')[0]
header=header.replace('CLEAN DESIGN REFERENCE','WORKING PHOTO FRAME').replace('// Continuous design geometry: no part divisions or manufacturing features.','// Separate working copy: rear rabbets, thin backers and printed sliding retainers.\n// Clean reference is read-only. Front artwork is copied without outline changes.')
header=header.replace('view_mode = "model"; // [model:3D reference, drawing:Flat front drawing]', '''view_mode = "assembly"; // [assembly:Complete assembly, frame:Frame without removable parts, exploded:Rear hardware exploded, backer:Selected backer, retainer:Sliding keeper, fit_sample:Local track fit sample, drawing:Flat front drawing]
show_backers = true;
show_retainers = true;
retainers_open = false;
backer_index = 1; // [1:8]

/* [Photo retention - finished mm] */
backer_thickness = 1.6;
photo_allowance = 0.4;
rabbet_overlap = 4;
backer_clearance = 0.3;
// Clearance per side. A small tapered rib provides sliding friction.
slide_clearance = 0.20;
lock_rib = 0.25;
exploded_distance = 30;
backer_colour = [0.48, 0.59, 0.65];
retainer_colour = [0.9, 0.56, 0.22];''')
header=header.replace('color(knot_colour) knot_reference();','color(knot_colour) photo_frame();')
header=header.replace('scale([uniform_scale, uniform_scale, uniform_scale])\n    if (view_mode == "drawing") reference_drawing();\n    else reference_model();','')
# Keep the reference's front view on opening; select fit_sample for a close-up.
header=header.replace('$vpd = overall_width * 2.75;', '$vpd = view_mode == "fit_sample" || view_mode == "retainer" ? 100 : overall_width * 2.75;')
data='photo_anchors = '+json.dumps(anchors)+';\nphoto_normals = '+json.dumps(normals)+';\nphoto_centres = '+json.dumps([[g.centroid.x,g.centroid.y] for g in loops])+';\n'
out=Path('working/Dara-Photo-Frame.scad')
out.write_text(header+Path('.work/photo_features.scad').read_text()+data+'\n// COPIED ARTWORK: edit this working file only.\n'+s[s.index('module knot_outline()'):]+ '\n'+ '\n'.join(scad_outline(f'photo_loop_{i+1}',g) for i,g in enumerate(loops)))
assert ref.read_bytes()==original
print('Updated working CAD: 8 backers, 32 identical sliders, integral T tracks; no screw holes.')

