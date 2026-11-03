from design_sections import *
import manifold3d as md, trimesh
from shapely.ops import linemerge
sys.path.insert(0,str(Path('scripts').resolve()))
from build_reference import scad_outline

def source_solid(name):
    text=Path('reference/tested-lap-joints/Tested-Lap-Joints.scad').read_text().split('module '+name+'() {')[1].split('\n}')[0]
    a,b=re.search(r'polyhedron\(points=(\[.*?\]),\s*faces=(\[.*?\]), convexity',text,re.S).groups()
    # OpenSCAD polyhedron uses clockwise faces, opposite Manifold.
    v=np.array(ast.literal_eval(a)); f=np.array(ast.literal_eval(b),dtype=np.uint64)[:,::-1].copy()
    s=md.Manifold(md.Mesh64(v,f))
    assert s.status()==md.Error.NoError
    assert s.volume()>0
    return s

def cross_shape(cs):
    out=Polygon()
    for ring in cs.to_polygons():out=out.symmetric_difference(Polygon(ring))
    return out

male=source_solid('straight_tongue').translate([-9.75,0,0])
female=source_solid('straight_socket').translate([28.518748855-9.75,0,0])
profile_region=box(-1,-.1,20,6.6)
MALE_PROFILE=cross_shape(male.rotate([-90,0,0]).slice(0)).intersection(profile_region).simplify(1e-6)
VOID_PROFILE=profile_region.difference(cross_shape(female.rotate([-90,0,0]).slice(0))).simplify(1e-6)
KEY=max([p for p in geoms(cross_shape(male.slice(5.9))) if p.centroid.x>1],key=lambda p:p.centroid.y)
key_y=KEY.centroid.y
KEY=affinity.translate(KEY,yoff=-key_y).simplify(1e-6)
POCKET=next(Polygon(r) for p in geoms(cross_shape(female.slice(5.9))) for r in p.interiors if Polygon(r).centroid.y>15 and Polygon(r).centroid.x>1)
POCKET=affinity.translate(POCKET,yoff=-key_y).simplify(1e-6)

def world(g,j):
    return affinity.translate(affinity.rotate(g,j['angle'],origin=(0,0)),*j['centre'])
def local(g,j):
    return affinity.rotate(affinity.translate(g,-j['centre'][0],-j['centre'][1]),-j['angle'],origin=(0,0))

def make_joint(p,q,j):
    domain=local(unary_union([p,q]),j).intersection(box(-1.5,-j['span']/2-22,20,j['span']/2+22))
    domain=max(geoms(domain),key=lambda poly:poly.intersection(box(-.1,-j['span']/2,.1,j['span']/2)).area)
    safe=[]
    for y in np.arange(-j['span']/2+4,j['span']/2-3,.25):
        if domain.covers(affinity.translate(POCKET.buffer(2),yoff=y)):safe.append(float(y))
    if not safe:return None
    ys=[min(safe,key=lambda y:abs(y-j['span']*v)) for v in [-1/3,1/3]]
    if ys[1]-ys[0]<6:return None
    # The original body clips the lap. Expand this planning-only mask slightly
    # past exterior edges to avoid coincident rounded CAD boundaries.
    return dict(j,keys=ys,domain=mapping(world(domain,j).buffer(.1,join_style=2)))

def find_joints(parts):
    choices=[]
    for i,p in enumerate(parts):
        for k in range(i+1,len(parts)):
            q=parts[k];s=p.boundary.intersection(q.boundary)
            if s.geom_type=='MultiLineString':s=linemerge(s)
            for line in geoms(s,'LineString'):
                if line.length<1:continue
                a=np.array(line.coords[0]);b=np.array(line.coords[-1]);t=(b-a)/np.linalg.norm(b-a);n=np.array([t[1],-t[0]]);mid=(a+b)/2
                if not p.contains(Point(mid-n)):n=-n
                j={'male':i,'female':k,'centre':mid.tolist(),'angle':math.degrees(math.atan2(n[1],n[0])),'span':line.length,'line':mapping(line)}
                opts=[make_joint(p,q,j),make_joint(p,q,dict(j,male=k,female=i,angle=j['angle']+180))]
                choices.append([o for o in opts if o is not None])
    def acyclic(js):
        edges={i:set()for i in range(len(parts))}
        for j in js:edges[j['male']].add(j['female'])
        visited=set();active=set()
        def walk(n):
            if n in active:return False
            if n in visited:return True
            active.add(n)
            for k in edges[n]:
                if not walk(k):return False
            active.remove(n);visited.add(n);return True
        return all(walk(n)for n in edges)
    def solve(js):
        if len(js)==len(choices):return js
        for j in choices[len(js)]:
            g=shape(j['domain'])
            if any(g.intersection(shape(k['domain'])).area>.001 for k in js):continue
            if not acyclic(js+[j]):continue
            solution=solve(js+[j])
            if solution is not None:return solution
        return None
    joints=solve([])
    assert joints is not None,'No collision-free acyclic lap schedule'
    return joints

DATA={}
for name in ['frame','M']:
    r=json.loads(Path('.work/sections-'+name+'.json').read_text());parts=[shape(p) for p in r['parts']]
    if name=='M':
        pp=geoms(split(unary_union([parts[2],parts[5]]),LineString([(0,17),(500,52)])))
        pp.sort(key=lambda p:-p.centroid.y);parts[2]=pp[0];parts[5]=pp[1]
    joints=find_joints(parts)
    masks=[]; placements=[]
    for i,p in enumerate(parts):
        other=unary_union([q for k,q in enumerate(parts) if k!=i and q.distance(p)<.1]).buffer(.0375,join_style=2)
        mask=p.buffer(.15,join_style=2).difference(other)
        masks.append(mask)
        envelope=p
        for j in joints:
            if j['male']==i:
                envelope=envelope.union(shape(j['domain']).intersection(world(box(-1,-1000,18,1000),j)))
        maxdim,_,angle,bounds=fit(envelope)
        assert maxdim<=246,(name,i,maxdim)
        placements.append({'angle':angle,'centre':[(bounds[0]+bounds[2])/2,(bounds[1]+bounds[3])/2],'bounds':bounds,'size':[bounds[2]-bounds[0],bounds[3]-bounds[1]],'label':list(p.representative_point().coords[0])})
    # Full lap domains must be independent, including across disconnected bands.
    for a,j in enumerate(joints):
        for k in joints[a+1:]:
            overlap=shape(j['domain']).intersection(shape(k['domain'])).area
            assert overlap<.001,(name,'lap overlap',a,j['male'],j['female'],k['male'],k['female'],overlap)
    DATA[name]={'parts':[mapping(p)for p in parts],'masks':[mapping(p) for p in masks],'joints':joints,'placements':placements}

def arr(v):return json.dumps(v,separators=(',',':'))
def poly_module(name,g):return scad_outline(name,g)

header='''// DARA PHOTO FRAME - A1 STAGGERED KEYED LAP SECTIONS
// New manufacturing copy of Dara-Photo-Frame.scad; source/reference untouched.
// CAD ONLY. No slicing, supports, toolpaths, print project, or production meshes.
// 30 frame sections F1-F30; 6 letter sections M1-M6. Finished size 914.4 mm.
// Irregular angled seams, with no grid or four-way seam intersections.
// Exact shoulder profiles and key/pocket contours extracted from the frozen
// Tested-Lap-Joints.scad straight sample, in final mm (NO further 75% scaling).
// Same geometry follows curved rails by clipping to the original body outline.
// Lap 18 mm; tongue 4.8 mm; shoulder radius .75 mm; hidden gap .15 mm;
// visible gap .075 mm. Keys 13.5 x 3 x 1.2 mm, radius .6 mm;
// pockets have .15 mm XY clearance and .3 mm clearance above the keys.
// Two keys per seam, spaced across each local rail. No screw/boss features added.
// M retains its 10.5 mm body, with the same unscaled joint geometry.
// Full 36-inch model is fixed here: changing scale invalidates bed and fit checks.
// Section mode selects one part, rotates it flat in XY and centres it at Z=0.
// Layout is a review of separate 256 mm bed outlines, not a multi-part plate.
// See the assembly_order arrays below: lower each socket over earlier tongues.
// This keyed lap needs a suitable bonded assembly; it is not a locking fastener.
// Rear photo tracks and socket overhangs need support planning at slicing time.
// Keep the original backers/retainers and M-to-frame attachment as in the source.
// Source SHA256: dcd467893411bca2ddaefc2110132db8b98dfd855f9dfdf1902084aa4d63706b

/* [Sections] */
part_family = "frame"; // [frame:Frame F1-F30, M:Letter M1-M6]
section_index = 1; // [1:30]
colour_sections = true;
show_section_ids = false; // Preview annotations only; never part of an export.
joint_index = 1; // [1:42]
joint_separation = 12;

'''
source=SOURCE
source=source.replace('view_mode = "assembly"; // '+SOURCE.split('view_mode = "assembly"; // ')[1].split('\n')[0],
'view_mode = "assembly"; // [assembly:Sectioned assembly, frame:Sectioned frame, M:Sectioned M, exploded:Separate sections, section:One section at print origin, layout:Separate bed reviews, joint_detail:Selected lap pair, backer:Original photo backer, retainer:Original keeper, fit_sample:Original keeper fit, drawing:Original front drawing]')
source=source.replace('scale([uniform_scale,uniform_scale,uniform_scale]) working_model();','sectioned_model();')
source=source.replace('$vpd = view_mode == "fit_sample" || view_mode == "retainer" ? 100 : overall_width * 2.75;',
'$vpd = view_mode=="section" ? 600 : view_mode=="joint_detail" ? 220 : view_mode=="fit_sample" || view_mode=="retainer" ? 100 : overall_width*2.75;')

modules='''
// Section geometry is authored in finished mm outside the artwork scale.
assert(overall_width==914.4 && knot_depth==18 && letter_depth==14 &&
       fabric_back_z==12 && fabric_depth==.8 && letter_back_z==18,
       "Section map and tested fits require the original 36-inch dimensions");
assert(show_knot && show_fabric, "Section geometry requires the complete frame core");
assert(part_family=="frame" || part_family=="M");
function part_count(kind) = kind=="frame" ? 30 : 6;
function joint_list(kind) = kind=="frame" ? frame_joints : M_joints;
function placement_list(kind) = kind=="frame" ? frame_placements : M_placements;
function part_colour(i) = [[.72,.81,.85],[.92,.74,.51],[.65,.76,.58],
                           [.82,.64,.69],[.66,.67,.84],[.89,.85,.64]][i%6];
assert(section_index>=1 && section_index<=part_count(part_family) && floor(section_index)==section_index,
       "Select a section in the chosen family (frame 1..30, M 1..6)");

module original_body_mm(kind) {
    scale([uniform_scale,uniform_scale,uniform_scale])
        if(kind=="M") translate([0,0,-letter_back_z]) letter_reference();
        else union() { photo_frame(); fabric_reference(); }
}
module section_envelope(kind,i) {
    union() {
        part_mask(kind,i);
        for(k=[0:len(joint_list(kind))-1])
            if(joint_list(kind)[k][0]==i) joint_domain(kind,k);
    }
}
module local_frame_artwork(i,artwork) {
    intersection() {
        section_envelope("frame",i);
        scale([uniform_scale,uniform_scale])
            if(artwork=="knot") knot_outline();
            else if(artwork=="core") offset(delta=.15) fabric_outline();
            else fabric_pattern();
    }
}
module section_body_mm(kind,i) {
    if(kind=="M") original_body_mm(kind);
    else union() {
        // Clip the 2D artwork first so F5/F6 do not evaluate the entire frame
        // for each section. These are the unchanged source depths and pockets.
        render(convexity=40) difference() {
            union() {
                linear_extrude(height=knot_depth*uniform_scale,convexity=30) local_frame_artwork(i,"knot");
                linear_extrude(height=fabric_back_z*uniform_scale,convexity=30) local_frame_artwork(i,"core");
                for(t=frame_tracks[i]) scale([uniform_scale,uniform_scale,uniform_scale])
                    at_retainer(floor(t/4),t%4) track_blank_mm();
            }
            for(p=frame_photos[i]) translate([0,0,-.02])
                linear_extrude(height=backer_thickness+photo_allowance+.02,convexity=20)
                    scale([uniform_scale,uniform_scale]) offset(delta=u(rabbet_overlap)) photo_opening(p);
            for(t=frame_tracks[i]) scale([uniform_scale,uniform_scale,uniform_scale])
                at_retainer(floor(t/4),t%4) track_channel_mm();
        }
        translate([0,0,fabric_back_z*uniform_scale])
            linear_extrude(height=fabric_depth*uniform_scale,convexity=30) local_frame_artwork(i,"weave");
    }
}
module joint_at(j) {
    translate([j[2][0],j[2][1],0]) rotate([0,0,j[3]]) children();
}
module shoulder_prism(socket, span) {
    // The polygon's Y coordinate becomes Z; extrusion runs along the rail width.
    rotate([90,0,0]) linear_extrude(height=span+44,center=true,convexity=10)
        if(socket) tested_socket_void_xz(); else tested_tongue_xz();
}
module joint_tool(kind,k,socket=false) {
    j=joint_list(kind)[k];
    intersection() {
        translate([0,0,-.1]) linear_extrude(height=7) joint_domain(kind,k);
        joint_at(j) union() {
            shoulder_prism(socket,j[4]);
            for(y=j[5]) translate([0,y,socket ? 4.94 : 4.79])
                linear_extrude(height=socket ? 1.36 : 1.21,convexity=10)
                    if(socket) tested_key_pocket(); else tested_key();
        }
    }
}
module section_shape(kind,i) {
    render(convexity=50) difference() {
        intersection() {
            section_body_mm(kind,i);
            union() {
                translate([0,0,-5]) linear_extrude(height=35,convexity=30) part_mask(kind,i);
                for(k=[0:len(joint_list(kind))-1])
                    if(joint_list(kind)[k][0]==i) joint_tool(kind,k);
            }
        }
        for(k=[0:len(joint_list(kind))-1])
            if(joint_list(kind)[k][1]==i) joint_tool(kind,k,true);
    }
}
module print_section(kind,i) {
    p=placement_list(kind)[i];
    // Only parts carrying original rear tracks have Z=-3.2.
    translate([-p[1][0],-p[1][1],p[3]]) rotate([0,0,p[0]]) section_shape(kind,i);
}
module preview_id(kind,i,z=15) {
    if(show_section_ids && $preview) {
        p=placement_list(kind)[i][2];
        %color("black") translate([p[0],p[1],z])
            linear_extrude(height=.2) text(str(kind=="frame" ? "F" : "M",i+1),size=9,halign="center",valign="center");
    }
}
module section_group(kind,spread=0) {
    for(i=[0:part_count(kind)-1]) {
        p=placement_list(kind)[i][2];
        translate([spread*p[0]/450,spread*p[1]/450,0]) {
            color(colour_sections ? part_colour(i) : kind=="frame" ? knot_colour : letter_colour)
                section_shape(kind,i);
            preview_id(kind,i);
        }
    }
}
module sectioned_model() {
    if(view_mode=="section") print_section(part_family,section_index-1);
    else if(view_mode=="layout") {
        for(i=[0:part_count(part_family)-1]) translate([(i%5)*280,-floor(i/5)*280,0]) {
            color(part_colour(i)) print_section(part_family,i);
            if($preview) %translate([-128,-128,-.5]) cube([256,256,.4]);
        }
    } else if(view_mode=="joint_detail") {
        assert(joint_index>=1 && joint_index<=len(joint_list(part_family)));
        j=joint_list(part_family)[joint_index-1];
        for(side=[0:1]) color(part_colour(side)) translate([0,0,side*joint_separation])
            intersection() {
                rotate([0,0,-j[3]]) translate([-j[2][0],-j[2][1],0]) section_shape(part_family,j[side]);
                translate([-24,-j[4]/2-12,-4]) cube([65,j[4]+24,22]);
            }
    } else if(view_mode=="frame") section_group("frame");
    else if(view_mode=="M") section_group("M");
    else if(view_mode=="assembly" || view_mode=="exploded") {
        section_group("frame",view_mode=="exploded" ? exploded_distance : 0);
        if(show_letter) translate([0,0,letter_back_z*uniform_scale+(view_mode=="exploded" ? exploded_distance : 0)])
            section_group("M",view_mode=="exploded" ? exploded_distance : 0);
        scale([uniform_scale,uniform_scale,uniform_scale]) {
            if(show_backers) color(backer_colour)
                translate([0,0,view_mode=="exploded" ? -u(exploded_distance) : 0])
                    for(i=[0:7]) photo_backer(i);
            if(show_retainers) color(retainer_colour)
                for(i=[0:7],j=[0:3]) at_retainer(i,j)
                    translate([retainers_open ? 12 : 0,0,view_mode=="exploded" ? -exploded_distance-8 : 0]) slider_mm();
        }
    } else scale([uniform_scale,uniform_scale,uniform_scale]) working_model();
}
'''
data='\n// Fixed seam schedule: [tongue part, socket part, XY, normal angle, span, key Y offsets].\n'
data+='// Assembly orders are 1-based section IDs; the joint records are 0-based.\n'
for name,d in DATA.items():
    js=[[j['male'],j['female'],j['centre'],j['angle'],j['span'],j['keys']]for j in d['joints']]
    placements=[]
    for p,pl in zip(d['parts'],d['placements']):
        shift=3.2 if name=='frame' and shape(p).intersects(unary_union(TRACKS)) else 0
        placements.append([pl['angle'],pl['centre'],pl['label'],shift])
    data+=name+'_joints = '+arr(js)+';\n'+name+'_placements = '+arr(placements)+';\n'
    incoming={i:set()for i in range(len(d['parts']))}
    for j in d['joints']:incoming[j['female']].add(j['male'])
    order=[]
    while len(order)<len(incoming):order.append(next(i for i,v in incoming.items()if i not in order and v.issubset(order)))
    data+=name+'_assembly_order = '+arr([i+1 for i in order])+';\n'
    if name=='frame':
        data+='frame_tracks = '+arr([[k for k,t in enumerate(TRACKS)if shape(p).intersects(t)]for p in d['parts']])+';\n'
        data+='frame_photos = '+arr([[k for k in range(8)if shape(p).distance(outline('photo_loop_'+str(k+1)))<25]for p in d['parts']])+';\n'
    for i,p in enumerate(d['masks']):data+=poly_module(f'{name}_mask_{i}',shape(p))
    for i,j in enumerate(d['joints']):data+=poly_module(f'{name}_joint_domain_{i}',shape(j['domain']))
data+='module part_mask(kind,i) {\n'
for name,d in DATA.items():
    for i in range(len(d['parts'])):data+=f'    if(kind=="{name}" && i=={i}) {name}_mask_{i}();\n'
data+='}\nmodule joint_domain(kind,i) {\n'
for name,d in DATA.items():
    for i in range(len(d['joints'])):data+=f'    if(kind=="{name}" && i=={i}) {name}_joint_domain_{i}();\n'
data+='}\n'
for name,g in [('tested_tongue_xz',MALE_PROFILE),('tested_socket_void_xz',VOID_PROFILE),('tested_key',KEY),('tested_key_pocket',POCKET)]:data+=poly_module(name,g)

output=Path('working/Dara-Photo-Frame-A1-Jointed.scad')
output.write_text(header+source+'\n'+modules+data)
Path('.work/jointed-data.json').write_text(json.dumps(DATA))
Path('.work/joint-profiles.json').write_text(json.dumps({name:mapping(g)for name,g in [('male',MALE_PROFILE),('void',VOID_PROFILE),('key',KEY),('pocket',POCKET)]}))
print('Wrote',output,output.stat().st_size)
for name,d in DATA.items():print(name,len(d['parts']),'parts',len(d['joints']),'joints','max footprint',max(max(p['size'])for p in d['placements']))

