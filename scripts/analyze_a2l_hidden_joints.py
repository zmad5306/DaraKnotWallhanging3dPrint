"""Third A2L partition study: minimize exposed frame seams behind the actual M.

Uses fresh cuts in continuous artwork. Never reads the preceding A2L layout.
Requires numpy, scipy, shapely >=2, Pillow. Produces geometry studies, not G-code.
"""
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

import analyze_a2l_partitions as a
from shapely.geometry import LineString, Point, shape, mapping
from shapely import polygons as triangle_polygons
from PIL import Image, ImageDraw, ImageFont

OUT = a.ROOT / 'working/review/a2l-hidden-joints'
s = a.CAD.read_text()
K = a.artwork(s, 'knot_outline')
F = a.artwork(s, 'fabric_outline')
W = K.union(F.buffer(.1125, join_style=2))
M = shape(json.loads((OUT / 'M-shadow.json').read_text())['shadow'])
SAFE = M.buffer(-2)
rows = json.loads((OUT / 'hidden-cut-catalog.json').read_text())
# This catalog is generated from the continuous stock, not existing F sections.
rows = [r for r in rows if shape(r['line']).difference(SAFE).length < .001]

def component(angle,offset,target):
 t=a.np.array([math.cos(math.radians(angle)),math.sin(math.radians(angle))]);n=a.np.array([-t[1],t[0]])
 return min(a.lines(W.intersection(LineString([n*offset-t*1000,n*offset+t*1000]))),key=lambda l:l.distance(Point(target)))
def arch(sign,target=140):
 r=[r for r in rows if tuple(sorted(r['rings']))==((3,6) if sign>0 else (3,9))]
 return shape(min(r,key=lambda r:abs(shape(r['line']).centroid.y-target)+.1*(r['length']-67))['line'])
def hidden_pair(pair,target):
 r=[r for r in rows if tuple(sorted(r['rings']))==tuple(sorted(pair))]
 return shape(min(r,key=lambda r:a.np.linalg.norm(a.np.array(shape(r['line']).centroid.coords[0])-target)+.02*r['length'])['line'])
def extend(l):
 xy=a.np.asarray([l.coords[0],l.coords[-1]]);v=xy[1]-xy[0];v/=a.np.linalg.norm(v)
 return LineString([xy[0]-v,xy[1]+v])

def evaluate(parts,seams,do_refine=False):
 central=[i for i,p in enumerate(parts) if p.covers(Point(-51,51)) or p.covers(Point(51,51))]
 order=sorted(range(len(parts)),key=lambda i:(0 if parts[i].interiors else 1 if i in central else 2,parts[i].centroid.y,parts[i].centroid.x))
 rank={v:i for i,v in enumerate(order)};env=list(parts);domains=[];recs=[]
 for i,j,l in seams:
  owner,partner=sorted([i,j],key=rank.get);xy=a.np.asarray([l.coords[0],l.coords[-1]]);mid=xy.mean(axis=0);t=(xy[1]-xy[0])/a.np.linalg.norm(xy[1]-xy[0]);n=a.np.array([-t[1],t[0]])
  if parts[owner].covers(Point(mid+n*.1)):n=-n
  t=a.np.array([-n[1],n[0]]);pad=22 if l.length>90 else 2
  def patch(lo,hi):return a.Polygon([mid+n*u+t*v for u,v in [(lo,-l.length/2-pad),(hi,-l.length/2-pad),(hi,l.length/2+pad),(lo,l.length/2+pad)]])
  stock=parts[owner].union(parts[partner]);ext=stock.intersection(patch(-1,18));dom=stock.intersection(patch(-1.5,20));domains.append(dom);env[owner]=env[owner].union(ext)
  recs.append(dict(tongue=owner+1,socket=partner+1,line=mapping(l),normal_deg=math.degrees(math.atan2(n[1],n[0])),length=l.length,xy_mm=mid.tolist(),padding_mm=pad,hidden=l.difference(SAFE).length<.001,exposed_mm=l.difference(M).length))
 fits=[a.fit(p,do_refine) for p in env]
 overlaps=[(i+1,j+1,p.intersection(q).area) for i,p in enumerate(domains) for j,q in enumerate(domains[:i]) if p.intersection(q).area>.001]
 return dict(fits=fits,domains=domains,envelopes=env,joints=recs,order=[i+1 for i in order],overlaps=overlaps)

def make_variant(mode=0,atop=140,bottom=-140,sidey=65):
 cuts=[]
 for sx in [-1,1]:
  for sy in [-1,1]:
   cuts.append(component(45 if sx*sy>0 else 135,0,(sx*237,sy*237)))
 for sy in [-1,1]:cuts.append(component(90,0,(0,sy*237)))
 for sx in [-1,1]:
  cuts.append(arch(sx,atop));cuts.append(component(0,bottom,(sx*51,bottom)))
  for sy in [-1,1]:
   bit=(0 if sx<0 else 2)+(0 if sy>0 else 1)
   if mode>>bit&1:
    cuts.append(hidden_pair((0,12 if sy>0 else 13) if sx<0 else (0,2 if sy>0 else 1),(sx*280,sy*51)))
    cuts.append(hidden_pair((9,12) if sy>0 else (11,13) if sx<0 else (1,4),(sx*237,sy*115))) if sx<0 else cuts.append(hidden_pair((2,6) if sy>0 else (1,4),(sx*237,sy*110)))
   else:
    pair=(0,(9 if sy>0 else 11) if sx<0 else (6 if sy>0 else 4))
    cuts.append(hidden_pair(pair,(sx*250,sy*sidey)))
 p=a.partition(W,[extend(l) for l in cuts]);j=a.shared_seams(p)
 return p,cuts,j

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def production_shadow_check():
    """Independently recover the front projection of the assembled copper parts."""
    tag = '{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
    poses = json.loads((a.ROOT/'working/geometry/hammered-M-assembly-poses.json').read_text())
    covers = json.loads((a.ROOT/'working/bambu/Dara-Photo-Frame-A1-Jointed/cover-crown-validation.json').read_text())['geometry_checks']
    pieces = []
    with zipfile.ZipFile(a.ROOT/'Dara.3mf') as z:
        for name, row in list(poses.items()) + [(r['name'], dict(path=r['mesh_path'])) for r in covers]:
            resources = ET.fromstring(z.read(row['path'])).find(tag+'resources')
            obj = next(o for o in resources if o.find(tag+'mesh') is not None and
                       ('part_id' not in row or o.get('id') == row['part_id']))
            mesh = obj.find(tag+'mesh')
            vertices = a.np.array([[float(e.get(k)) for k in ['x','y','z']] for e in mesh.find(tag+'vertices')])
            faces = a.np.array([[int(e.get(k)) for k in ['v1','v2','v3']] for e in mesh.find(tag+'triangles')])
            if 'assembly_from_mesh' in row:
                t = a.np.array(row['assembly_from_mesh'])
                vertices = vertices@t[:3,:3].T+t[:3,3]
            # Front-facing projections cover blind bores too, while preserving
            # the silhouette and gaps between parts. The five covers fill gaps.
            normals = a.np.cross(vertices[faces[:,1]]-vertices[faces[:,0]],
                                vertices[faces[:,2]]-vertices[faces[:,0]])[:,2]
            roof = faces[normals > 1e-7]
            pieces.append(a.union_all(triangle_polygons(vertices[roof,:2])))
    actual = a.union_all(pieces)
    assert actual.symmetric_difference(M).area < .0001
    nominal = a.artwork(s, 'letter_outline')
    assert actual.symmetric_difference(nominal).area < .05
    return dict(production_parts=6, copper_covers=5,
                cached_shadow_error_mm2=actual.symmetric_difference(M).area,
                nominal_outline_difference_mm2=actual.symmetric_difference(nominal).area,
                projection='front view along the wall normal')


def classify(line):
    if line.difference(SAFE).length < .001:
        return 'fully_hidden'
    if line.intersection(M).length > .001:
        return 'partly_covered'
    return 'fully_exposed'


def search():
    results = []
    tested = 0
    for mode in [0, 15]:
        best = None
        for atop in range(128, 157, 2):
            for bottom in range(-160, -125, 2):
                tested += 1
                parts, cuts, seams = make_variant(mode, atop, bottom)
                detail = evaluate(parts, seams)
                maxfit = max(f['utilization'] for f in detail['fits'])
                if detail['overlaps'] or maxfit > 1:
                    continue
                counts = {k:0 for k in ['fully_hidden','partly_covered','fully_exposed']}
                exposed_length = 0
                for _, _, line in seams:
                    counts[classify(line)] += 1
                    exposed_length += line.difference(M).length
                # A partial seam is exposed. Do not reward extra concealed cuts:
                # after visibility and exposed length, prefer fewer total joints.
                objective = (counts['partly_covered']+counts['fully_exposed'],
                             round(exposed_length), len(seams), maxfit)
                if best is None or objective < best[0]:
                    best = (objective, atop, bottom)
        objective, atop, bottom = best
        parts, cuts, seams = make_variant(mode, atop, bottom)
        detail = evaluate(parts, seams, True)
        results.append(dict(mode=mode, objective=list(objective), arch_target_mm=atop,
                            lower_cut_y_mm=bottom, parts=parts, seams=seams, detail=detail))
    # Check every mixed single/double-joint arrangement at the winning locations.
    for mode in range(1,15):
        parts, cuts, seams = make_variant(mode, results[0]['arch_target_mm'], results[0]['lower_cut_y_mm'])
        detail = evaluate(parts,seams)
        tested += 1
        assert sum(classify(l)!='fully_hidden' for _,_,l in seams) == 8
        assert len(seams) >= 14
    return results, tested


def hardware_conflicts(domains):
    records = []
    sites = []
    for kind, table, radius in [('M screw',a.array(s,'screw_mounts'),8.5),
                                ('M locator',a.array(s,'dowel_mounts'),4)]:
        sites.extend((kind,k+1,a.Point(row[2]).buffer(radius)) for k,row in enumerate(table))
    anchors = a.np.asarray(a.array(s,'photo_anchors'))*.75
    normals = a.np.asarray(a.array(s,'photo_normals'))
    sites.extend(('photo pilot',k+1,a.Point(xy).buffer(4.6)) for k,xy in
                 enumerate((anchors+normals*9.5).reshape(-1,2)))
    for kind,index,g in sites:
        hits = [i+1 for i,d in enumerate(domains) if g.intersection(d).area > .001]
        if hits:
            records.append(dict(kind=kind,index=index,joints=hits))
    return records


def package(result):
    parts, detail = result['parts'], result['detail']
    counts = {k:0 for k in ['fully_hidden','partly_covered','fully_exposed']}
    for row in detail['joints']:
        line = shape(row['line'])
        row['visibility'] = classify(line)
        row['M_edge_clearance_mm'] = line.distance(M.boundary) if row['visibility']=='fully_hidden' else 0
        counts[row['visibility']] += 1
    joined = a.union_all(parts)
    coverage = joined.symmetric_difference(W).area
    overlap = sum(p.intersection(q).area for i,p in enumerate(parts) for q in parts[:i])
    assert coverage < 1e-6 and overlap < 1e-7
    assert not detail['overlaps'] and max(f['utilization'] for f in detail['fits']) < 1
    assert all(p.geom_type=='Polygon' and p.is_valid for p in parts)
    # A tongue may overlap its socket's stock in XY; it must not enter a third
    # part's stock, which would invalidate the assembled joint construction.
    invasion = max(env.difference(parts[i].union(a.union_all([
        parts[j['socket']-1] for j in detail['joints'] if j['tongue']==i+1]))).area
        for i,env in enumerate(detail['envelopes']))
    assert invasion < 1e-6
    order = {p:i for i,p in enumerate(detail['order'])}
    assert all(order[j['tongue']]<order[j['socket']] for j in detail['joints'])
    walls = a.wall_sites(parts, detail['domains'], K, s)
    return dict(mode=result['mode'], arch_target_mm=result['arch_target_mm'], lower_cut_y_mm=result['lower_cut_y_mm'],
                sections=len(parts), total_joints=len(detail['joints']), **counts,
                exposed_joints=counts['partly_covered']+counts['fully_exposed'],
                exposed_seam_length_mm=sum(shape(j['line']).difference(M).length for j in detail['joints']),
                concealed_seam_length_mm=sum(shape(j['line']).intersection(M).length for j in detail['joints']),
                minimum_full_concealment_margin_mm=min(j['M_edge_clearance_mm'] for j in detail['joints'] if j['visibility']=='fully_hidden'),
                bed_mm=[330,320], usable_bed_mm=[327,317], lap_length_mm=18,
                coverage_error_mm2=coverage, nominal_part_overlap_mm2=overlap,
                maximum_lap_domain_overlap_mm2=0, third_part_lap_invasion_mm2=invasion,
                assembly_order=detail['order'], part_fits=detail['fits'],
                minimum_joint_length_mm=min(j['length'] for j in detail['joints']),
                maximum_joint_length_mm=max(j['length'] for j in detail['joints']),
                rear_hardware_conflicts=hardware_conflicts(detail['domains']), wall_mount_candidates=walls,
                joints=detail['joints'], parts=[mapping(p) for p in parts],
                lap_envelopes=[mapping(p) for p in detail['envelopes']])


def render(report,name):
    im = Image.new('RGB',(2200,1280),'#f5f2ec'); d=ImageDraw.Draw(im)
    font='/System/Library/Fonts/Supplemental/Arial.ttf'
    title=ImageFont.truetype(font,32); body=ImageFont.truetype(font,23); small=ImageFont.truetype(font,19)
    colors=['#afcbd4','#e4cbb0','#b9cdb5','#d0bed7','#ddc7a2','#b7c4de','#e0bdc7','#c4d8bd','#c9d8ce','#dfd3b1']
    def coords(xy,ox,oy=650):return [(ox+x,oy-y) for x,y in xy]
    def fill(g,color,ox):
        mask=Image.new('L',im.size);md=ImageDraw.Draw(mask)
        for p in a.polygons(g):
            md.polygon(coords(p.exterior.coords,ox),fill=255)
            for r in p.interiors:md.polygon(coords(r.coords,ox),fill=0)
        im.paste(color,(0,0),mask)
    for i,p in enumerate(report['parts']):
        g=shape(p);fill(g,colors[i%len(colors)],550)
        x,y=g.representative_point().coords[0]
        d.text((550+x,650-y),str(i+1),font=small,fill='#203342',anchor='mm')
    for p in a.polygons(M):
        d.line(coords(p.exterior.coords,550),fill='#a77a52',width=2)
    fill(W,'#fffdf7',1650);fill(F,'#c2ab84',1650)
    for row in report['joints']:
        line=shape(row['line'])
        d.line(coords(line.coords,550),fill='#278062' if row['visibility']=='fully_hidden' else '#b64132',width=4)
        for l in a.lines(line.difference(M)):
            d.line(coords(l.coords,1650),fill='#b64132',width=4)
    fill(M,'#b77b53',1650)
    d.text((75,65),f'Third layout: {report["total_joints"]} joints / {report["fully_hidden"]} fully hidden',font=title,fill='#203342')
    d.text((1175,65),f'M installed: {report["exposed_joints"]} joints remain exposed',font=title,fill='#203342')
    d.text((1100,1165),'Green = fully behind M with 2 mm margin. Red = at least partly visible.',font=body,fill='#334a59',anchor='mm')
    d.text((1100,1215),'Fresh continuous-artwork partitions; 18 mm lap footprints checked. Production remeshing and native slicing pending.',font=small,fill='#596771',anchor='mm')
    im.save(OUT/name)


def main():
    sources=json.loads((OUT/'sources.json').read_text())
    assert sha(a.CAD)==sources['cad_sha256']
    assert sha(a.ROOT/'Dara.3mf')==sources['project_sha256']
    projection=production_shadow_check()
    results,tested=search()
    reports=[package(r) for r in results]
    summaries=[]
    for report in reports:
        name='lean' if report['mode']==0 else 'more-hidden'
        (OUT/(name+'-candidate.json')).write_text(json.dumps(report,indent=2)+'\n')
        render(report,name+'-layout.png')
        summaries.append({k:v for k,v in report.items() if k not in ['parts','lap_envelopes','joints']})
    proof=dict(status='third geometry partition study; production meshes and G-code not regenerated',
               objective=['minimize joints with any visible portion','minimize exposed seam length to nearest mm',
                          'minimize total joints','minimize worst bed utilization'],
               sources=sources,production_M_projection_check=projection,
               catalog_accepted_cross_sections=len(rows), layouts_evaluated=tested,
               full_concealment_margin_mm=2, variants=summaries,
               recommendation='lean: same eight exposed joints with four fewer concealed assembly joints',
               limitations=['Search result, not a proven global minimum.',
                            'Counts describe frontal coverage; oblique views may reveal seams under the raised M.',
                            'Rear attachments listed as conflicts require relocation and matching M/frame regeneration.',
                            'No production mesh, material modifier, support, purge tower or native G-code validation.'])
    (OUT/'verification.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k!='variants'},indent=2))
    for r in summaries:
        print(json.dumps({k:v for k,v in r.items() if k in ['sections','total_joints','fully_hidden','partly_covered','fully_exposed','exposed_joints','exposed_seam_length_mm','minimum_full_concealment_margin_mm','maximum_joint_length_mm','rear_hardware_conflicts']},indent=2))


if __name__=='__main__':
    main()
