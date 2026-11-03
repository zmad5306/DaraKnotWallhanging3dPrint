from pathlib import Path
p=Path('working/Dara-Photo-Frame-A1-Jointed.scad');s=p.read_text()
a='''    if($preview && fast_preview && cached_shape_matches(kind)) {
        // Embedded meshes predate the wall slots. Apply live slot cuts AFTER the
        // cache so every clearance setting matches native F6/section geometry.
        if(kind=="frame" && has_wall_slots(i)) render(convexity=50) difference() {
            preview_section(kind,i);
            wall_slots_for_section(i);
        } else preview_section(kind,i);
    }'''
assert a in s
s=s.replace(a,'    if($preview && fast_preview && cached_shape_matches(kind)) preview_section(kind,i);')
s=s.replace('function cached_shape_matches(kind) = fabric_style', '''// The four revised preview meshes include their default rear slots.
// Any slot geometry change falls back to native CSG, including moved mounts.
function wall_cached_shape_matches() =
    wall_mounts==[[2,[-196,222],-6,[4,54]],[4,[196,222],-6,[-54,14]],
                  [15,[-196,-222],6,[-14,52]],[17,[196,-222],6,[-54,54]]] &&
    wall_key_clearance==.2 && wall_key_depth_clearance==.3 &&
    wall_key_width==20 && wall_key_height==10 && wall_key_projection==3;
function cached_shape_matches(kind) = (kind=="M" || wall_cached_shape_matches()) && fabric_style''')
s=s.replace('translate([-m[1][0],-m[1][1],0]) section_shape("frame",m[0]);','translate([-m[1][0],-m[1][1],0]) section_csg("frame",m[0]);')
p.write_bytes(s.replace('\n','\r\n').encode())
p=Path('.work/check_wall_blocks.py');s=p.read_text()
s=s.replace(' add(f\'F{owner+1}-cached\',f\'difference() {{ preview_section("frame",{owner}); wall_slots_for_section({owner}); }}\')','')
s=s.replace(' name,path,extra=job\n',' name,path,extra=job\n if (OUT/f\'{name}.stl\').exists() and (OUT/f\'{name}.log\').exists() and \'ERROR:\' not in (OUT/f\'{name}.log\').read_text() and \'WARNING:\' not in (OUT/f\'{name}.log\').read_text(): return\n')
s=s.replace('def load(name):','if \'--render-only\' in sys.argv: sys.exit(0)\ndef load(name):')
p.write_text(s)
