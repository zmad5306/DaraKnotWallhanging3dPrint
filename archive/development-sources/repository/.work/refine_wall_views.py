from pathlib import Path
p=Path('working/Dara-Photo-Frame-A1-Jointed.scad');s=p.read_text();s=s.replace('check the actual hardware and bonded fit first.','check the actual hardware and key fit first.')
s=s.replace('wall_mount_detail" || view_mode=="wall_keyhole_detail" ? [120,0,20]', 'wall_keyhole_detail" ? [75,0,80] : view_mode=="wall_mount_detail" ? [120,0,20]')
s=s.replace('$vpd = view_mode=="wall_block"', '$vpd = view_mode=="wall_keyhole_detail" ? 120 : view_mode=="wall_block"')
a='''    color(wall_block_colour) difference() {
        wall_block_mm(wall_mount_index-1);
        translate([wall_keyhole_x,-30,-1]) cube([40,60,wall_standoff+6]);
    }'''
b='''    color(wall_block_colour) render(convexity=20) intersection() {
        wall_block_mm(wall_mount_index-1);
        translate([wall_keyhole_x-15,-wall_block_height/2-1,-.02])
            cube([15,wall_block_height+2,wall_standoff+wall_key_projection+1]);
    }'''
assert a in s;s=s.replace(a,b);p.write_bytes(s.replace('\n','\r\n').encode())
p=Path('.work/render_wall_blocks.py');s=p.read_text()
a=" values=cam.split(','); extra=extra+['-D','$vpr=['+','.join(values[3:6])+']','-D','$vpt=['+','.join(values[:3])+']','-D','$vpd='+values[6]]\n"
s=s.replace(a,'')
s=s.replace("'0,0,0,180,0,180,360'", "'0,0,0,150,0,180,360'").replace("'40,0,5,65,0,280,330'", "'0,0,0,75,0,80,120'")
s=s.replace("jobs=[", "import re\nrender_source=re.sub(r'^\\$vp[trd] = .*?;.*$', '', CAD.read_text(), flags=re.M)\nrender_path=Path('.work/wall-blocks-screwed/render.scad');render_path.write_text(render_source);CAD=render_path\njobs=[")
p.write_text(s)
