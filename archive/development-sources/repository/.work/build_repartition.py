from repartition_search import *
import graphlib
sys.path.insert(0,str(Path('scripts').resolve()))
from build_reference import scad_outline
CAD=Path('working/Dara-Photo-Frame-A1-Jointed.scad')
s=Path('.work/repartition-before.scad').read_text()
D=json.loads((OUT/'jointed-data.json').read_text());mounts=json.loads((OUT/'mount-plan.json').read_text())
jd=lambda v:json.dumps(v,separators=(',',':'))
def assign(name,v):
 global s
 s,n=re.subn(r'^'+name+r' = .*?;',lambda _:name+' = '+jd(v)+';',s,flags=re.M);assert n==1,name
screws=[[r['m'],r['frame'],r['xy']]for r in mounts['screws']];pins=[[r['m'],r['frame'],r['xy'],int(r['slot']),r['angle']]for r in mounts['pins']]
for name,v in [('screw_mounts',screws),('dowel_mounts',pins),('mount_cache_screws',screws),('mount_cache_dowels',pins)]:assign(name,v)
s=s.replace('mount_preview_ready = true;','mount_preview_ready = false;').replace('photo_preview_ready = true;','photo_preview_ready = false;')
# Retain all original art and mounting modules, replace only partition data.
profiles=s[s.index('module tested_tongue_xz()'):s.index('module preview_frame_0()')]
s=s[:s.index('frame_joints =')]
for kind,d in D.items():
 ps=list(map(shape,d['parts']));js=d['joints'];placements=[];masks=[];footprints=[];retainers=[];photos=[]
 for i,p in enumerate(ps):
  rest=unary_union([q for k,q in enumerate(ps)if k!=i]);mask=p.buffer(.15,join_style=2).difference(rest.buffer(.0375,join_style=2));masks.append(mask)
  env=envelope(p,js);size,angle,b=fast_fit(env,True)
  # 0.025-degree refined flat rotation; never tilt or stand sections upright.
  centre=[(b[0]+b[2])/2,(b[1]+b[3])/2]
  placements.append([angle,centre,list(p.representative_point().coords[0]),0]);footprints.append([b[2]-b[0],b[3]-b[1],16.5 if kind=='frame' and any(r[1]==i for r in pins) else 13.5 if kind=='frame' else 10.5])
  if kind=='frame':
   stock=unary_union([mask,*[shape(j['domain'])for j in js if j['male']==i]])
   retainers.append([k for k,piv in enumerate(PHOTO_PIVOTS)if stock.distance(Point(piv))<2])
   photos.append([k for k in range(8)if stock.intersects(outline('photo_loop_'+str(k+1)).buffer(4.5))])
 graph={i:set()for i in range(len(ps))}
 for j in js:graph[j['female']].add(j['male'])
 order=[i+1 for i in graphlib.TopologicalSorter(graph).static_order()]
 s+=kind+'_joints = '+jd([[j['male'],j['female'],j['centre'],j['angle'],j['span'],j['keys']]for j in js])+';\n'
 s+=kind+'_placements = '+jd(placements)+';\n'
 s+=kind+'_assembly_order = '+jd(order)+';\n'
 s+=kind+'_print_footprints = '+jd(footprints)+';\n'
 if kind=='frame':
  assert sorted(t for r in retainers for t in r)==list(range(32))
  s+='frame_retainers = '+jd(retainers)+';\nframe_photos = '+jd(photos)+';\n'
 for i,mask in enumerate(masks):s+=scad_outline(f'{kind}_mask_{i}',mask)+'\n'
 for i,j in enumerate(js):s+=scad_outline(f'{kind}_joint_domain_{i}',shape(j['domain']))+'\n'
 d['placements']=placements;d['masks']=[mapping(m)for m in masks];d['footprints']=footprints;d['assembly_order']=order
for mod,suffix,collection in [('part_mask','mask','parts'),('joint_domain','joint_domain','joints')]:
 s+=f'module {mod}(kind,i) {{\n'
 for kind,d in D.items():
  for i in range(len(d[collection])):s+=f'    if(kind=="{kind}" && i=={i}) {kind}_{suffix}_{i}();\n'
 s+='}\n'
s+=profiles
s+='// Preview tessellations are regenerated after native geometry validation.\nmodule preview_section(kind,i) { section_csg(kind,i); }\n'
s=s.replace('30 frame sections F1-F30','20 frame sections F1-F20').replace('Frame F1-F30','Frame F1-F20').replace('section_index = 1; // [1:30]','section_index = 1; // [1:20]').replace('joint_index = 1; // [1:42]','joint_index = 1; // [1:31]').replace('kind=="frame" ? 30 : 6','kind=="frame" ? 20 : 6').replace('frame 1..30, M 1..6','frame 1..20, M 1..6')
s=s.replace('// Original backers, artwork, lap seams and overall front height are preserved.','// Original backers, artwork, tested lap profile and overall front height are preserved.')
s=s.replace('// Irregular angled seams, with no grid or four-way seam intersections.','// Repartitioned from continuous outlines: 31 frame laps + 5 M laps (previously 42 + 5).\n// Irregular angled seams, with no grid or four-way seam intersections.\n// All sections fit a 253 mm square including tongues at the saved flat rotations.\n// A1 printable area: 256 x 256 mm; at least 1.5 mm per edge, before any brim.\n// Separate bed outlines are review aids; layout does not represent one loaded plate.')
s=s.replace('show_section_ids = false;', 'show_plate_outline = false; // Preview the A1 bed around a single section.\nshow_section_ids = false;')
s=s.replace('function part_count(kind)', 'a1_plate_size = 256;\na1_edge_allowance = 1.5;\nfunction print_footprints(kind) = kind=="frame" ? frame_print_footprints : M_print_footprints;\nfunction part_count(kind)')
s=s.replace('module print_section(kind,i) {','module print_section(kind,i) {\n    dims=print_footprints(kind)[i];\n    assert(max(dims[0],dims[1])<=a1_plate_size-2*a1_edge_allowance, "Section exceeds A1 bed allowance");')
s=s.replace('else if(view_mode=="section") print_section(part_family,section_index-1);','''else if(view_mode=="section") {
        print_section(part_family,section_index-1);
        if($preview && show_plate_outline) a1_plate_outline();
        echo(section=str(part_family=="frame" ? "F" : "M",section_index),
             footprint_mm=print_footprints(part_family)[section_index-1],
             flat_rotation_deg=placement_list(part_family)[section_index-1][0]);
    }''')
s=s.replace('if($preview) %translate([-128,-128,-.5]) cube([256,256,.4]);','''if($preview) {
                a1_plate_outline();
                %color("black") translate([-123,-123,17]) linear_extrude(height=.2)
                    text(str(part_family=="frame" ? "F" : "M",i+1),size=10);
            }''')
s=s.replace('module sectioned_model() {','''module a1_plate_outline() {
    // Background geometry never appears in a native render/export.
    %color([.3,.35,.4,.3]) translate([0,0,-.5]) linear_extrude(height=.3)
        difference() { square([256,256],center=true); square([253,253],center=true); }
}
module sectioned_model() {''')
s=s.replace(': [0,0,0];\n$vpr', ': view_mode=="layout" ? [560,-floor((part_count(part_family)-1)/5)*140,0] : [0,0,0];\n$vpr',1)
CAD.write_text(s)
(OUT/'jointed-data.json').write_text(json.dumps(D))
print('New CAD written',len(s),'characters; 20 frame + 6 M sections')
