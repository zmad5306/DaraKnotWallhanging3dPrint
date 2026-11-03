from pathlib import Path
import sys,re,ast,math,hashlib,json
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
from shapely.geometry import Polygon,Point
from shapely import affinity
sys.path.insert(0,str(Path('scripts').resolve()))
from build_reference import scad_outline
ref=Path('reference/Dara-Clean-Reference.scad'); original=ref.read_bytes(); s=original.decode()
a,b=re.findall(r'polygon\(points = (\[.*?\]), paths = (\[.*?\]), convexity',s,re.S)[0]
pts=ast.literal_eval(a); paths=ast.literal_eval(b)
rails=Polygon([pts[j] for j in paths[0]],[[pts[j] for j in path] for path in paths[1:]])
loops=[Polygon(r) for r in rails.interiors if 19000<Polygon(r).area<21000]
loops.sort(key=lambda g: -math.atan2(g.centroid.y,g.centroid.x))
assert len(loops)==8
anchors=[]; normals=[]
for g in loops:
 ring=g.exterior; aa=[]; nn=[]
 for f in (.125,.375,.625,.875):
  p=ring.interpolate(f,normalized=True); q=ring.interpolate((f+.0001),normalized=True)
  dx,dy=q.x-p.x,q.y-p.y; length=math.hypot(dx,dy); n=(-dy/length,dx/length)
  if g.contains(Point(p.x+n[0],p.y+n[1])): n=(-n[0],-n[1])
  aa.append([p.x,p.y]); nn.append(n)
  centre=Point(p.x+n[0]*5.5/.75,p.y+n[1]*5.5/.75)
  assert rails.covers(centre.buffer(4.8/.75)), 'Screw seat escapes rail'
 assert rails.union(g).covers(g.buffer(4/.75)), 'Rabbet escapes rail'
 anchors.append(aa); normals.append(nn)
header=s.split('// FROZEN ARTWORK OUTLINES')[0]
header=header.replace('CLEAN DESIGN REFERENCE','WORKING PHOTO FRAME').replace('// Continuous design geometry: no part divisions or manufacturing features.','// Working copy: rear photo rabbets and removable screw-retained backers.')
header=header.replace('view_mode = "model"; // [model:3D reference, drawing:Flat front drawing]','view_mode = "assembly"; // [assembly:Frame with backers, frame:Frame only, exploded:Backers pulled rearward, backer:One backer for printing, backers:All backers for printing, drawing:Flat front drawing]\nshow_backers = true;\nbacker_index = 1; // [1:8]\n\n/* [Photo hardware - finished millimetres, not scaled] */\nbacker_thickness = 1.6;\nphoto_allowance = 0.4;\nrabbet_overlap = 4;\nbacker_clearance = 0.3;\nscrew_offset = 5.5;\nscrew_seat_radius = 4.5;\nscrew_pilot_diameter = 2.0;\nscrew_clearance_diameter = 2.8;\nscrew_pilot_depth = 5.5;\nexploded_distance = 30;')
header=header.replace('color(knot_colour) knot_reference();','color(knot_colour) photo_frame();')
old='scale([uniform_scale, uniform_scale, uniform_scale])\n    if (view_mode == "drawing") reference_drawing();\n    else reference_model();'
header=header.replace(old,'')
features='''// All manufacturing dimensions above are in finished mm; artwork is master units.
function u(mm) = mm / uniform_scale;
function screw_xy(i,j) = photo_anchors[i][j] + photo_normals[i][j] * u(screw_offset);
assert(backer_index >= 1 && backer_index <= 8 && floor(backer_index)==backer_index);
assert(backer_thickness > 0 && photo_allowance > 0);
assert(backer_clearance > 0 && backer_clearance < rabbet_overlap);
assert(screw_pilot_diameter > 0 && screw_clearance_diameter > screw_pilot_diameter);
assert(screw_seat_radius > screw_clearance_diameter/2 + backer_clearance + 1);
assert(screw_offset < rabbet_overlap + screw_seat_radius - backer_clearance - 1);
assert(backer_thickness + screw_pilot_depth < knot_depth*uniform_scale - 2);
assert(backer_thickness + photo_allowance < knot_depth*uniform_scale - 2);

module photo_opening(i) {
    if (i==0) photo_loop_1();
    if (i==1) photo_loop_2();
    if (i==2) photo_loop_3();
    if (i==3) photo_loop_4();
    if (i==4) photo_loop_5();
    if (i==5) photo_loop_6();
    if (i==6) photo_loop_7();
    if (i==7) photo_loop_8();
}
module screw_seats(i, clearance=0) {
    for (j=[0:3]) translate(screw_xy(i,j))
        circle(r=u(screw_seat_radius + clearance), $fn=48);
}
// Rear entrance at Z=0. Main pocket holds backer + photo; ear pockets
// stop at the backer face, leaving solid rail above each screw seat.
// That solid shoulder supports the ears and receives a blind pilot hole.
module photo_frame() {
    difference() {
        knot_reference();
        for (i=[0:7]) {
            translate([0,0,-u(0.02)])
                linear_extrude(height=u(backer_thickness+photo_allowance+0.02))
                    offset(delta=u(rabbet_overlap)) photo_opening(i);
            translate([0,0,-u(0.02)])
                linear_extrude(height=u(backer_thickness+0.02)) screw_seats(i);
            for(j=[0:3]) translate(concat(screw_xy(i,j),[-u(0.02)]))
                cylinder(h=u(backer_thickness+screw_pilot_depth+0.02),
                         d=u(screw_pilot_diameter),$fn=32);
        }
    }
}
module photo_backer(i) {
    difference() {
        linear_extrude(height=u(backer_thickness)) union() {
            offset(delta=u(rabbet_overlap-backer_clearance)) photo_opening(i);
            screw_seats(i,-backer_clearance);
        }
        for (j=[0:3]) translate(concat(screw_xy(i,j),[-u(0.02)]))
            cylinder(h=u(backer_thickness+0.04),d=u(screw_clearance_diameter),$fn=32);
    }
}
module working_model() {
    if(view_mode=="drawing") reference_drawing();
    else if(view_mode=="backer")
        translate(-concat(photo_centres[backer_index-1],[0])) photo_backer(backer_index-1);
    else if(view_mode=="backers")
        for(i=[0:7]) translate([u((i%4)*155),u(floor(i/4)*155),0])
            translate(-concat(photo_centres[i],[0])) photo_backer(i);
    else {
        reference_model();
        if(show_backers && view_mode!="frame") color([0.48,0.59,0.65])
            translate([0,0,view_mode=="exploded" ? -u(exploded_distance) : 0])
                for(i=[0:7]) photo_backer(i);
    }
}
scale([uniform_scale,uniform_scale,uniform_scale]) working_model();

'''
data='photo_anchors = '+json.dumps(anchors)+';\nphoto_normals = '+json.dumps(normals)+';\nphoto_centres = '+json.dumps([[g.centroid.x,g.centroid.y] for g in loops])+';\n'
out=Path('working');out.mkdir(exist_ok=True)
(out/'Dara-Photo-Frame.scad').write_text(header+features+data+'\n// COPIED ARTWORK: edit this working file only.\n'+s[s.index('module knot_outline()'):]+ '\n'+ '\n'.join(scad_outline(f'photo_loop_{i+1}',g) for i,g in enumerate(loops)))
assert ref.read_bytes()==original
(out/'reference-sha256.txt').write_text(hashlib.sha256(original).hexdigest()+'  reference/Dara-Clean-Reference.scad\n')
print('Created self-contained working CAD; 8 pockets and 32 screw seats fit inside existing rails.')
