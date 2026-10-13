"""Reapply the existing seam lines to the clean continuous frame artwork.

Old section masks and lap trimming domains contained the traced artwork too.
Rebuilding only knot_outline therefore clipped new curves back to old waves.
This rebuild retains every seam centre, angle, key and manufacturing profile.
"""
import json, math, re
from validate_print_project import ROOT, CAD, digest
from build_jointed_bambu_project import read_array
from add_blue_ribbon_edge import artwork
from repair_curve_artifacts import serialize
from shapely import affinity, union_all
from shapely.geometry import LineString, box
from shapely.ops import polygonize

REVIEW=ROOT/'working/review/clean-edges'

def partition_shapes(cad):
    whole=artwork(cad,'knot_outline').union(artwork(cad,'fabric_outline').buffer(.1125,join_style=2))
    joints=read_array(cad,'frame_joints')
    cuts=[]
    for j in joints:
        a=math.radians(j[3]); tx,ty=-math.sin(a),math.cos(a); h=j[4]/2+4
        cuts.append(LineString([(j[2][0]-tx*h,j[2][1]-ty*h),(j[2][0]+tx*h,j[2][1]+ty*h)]))
    cells=[p for p in polygonize(union_all([whole.boundary,*cuts])) if whole.covers(p.representative_point())]
    assert len(cells)==20,len(cells)
    old=[affinity.scale(artwork(cad,f'frame_mask_{i}'),1/.75,1/.75,origin=(0,0)) for i in range(20)]
    indices=[max(range(20),key=lambda k:p.intersection(old[k]).area) for p in cells]
    assert sorted(indices)==list(range(20)),indices
    parts=[cells[indices.index(i)] for i in range(20)]
    assert union_all(parts).symmetric_difference(whole).area<1e-7
    masks=[]
    for i,p in enumerate(parts):
        rest=union_all([q for k,q in enumerate(parts) if k!=i])
        masks.append(p.buffer(.15,join_style=2).difference(rest.buffer(.0375,join_style=2)))
    domains=[]
    for j in joints:
        rect=affinity.translate(affinity.rotate(box(-1.5,-j[4]/2-22,20,j[4]/2+22),j[3],origin=(0,0)),*j[2])
        d=whole.intersection(rect)
        if d.geom_type=='MultiPolygon':
            d=max(d.geoms,key=lambda p:p.intersection(cuts[len(domains)]).length)
        domains.append(d.buffer(.1,join_style=2))
    for i,a in enumerate(domains):
        for b in domains[i+1:]:assert a.intersection(b).area<.001
    overlap=max(a.intersection(b).intersection(whole).area for i,a in enumerate(masks) for b in masks[i+1:])
    assert overlap<1e-7,overlap
    return masks,domains,dict(parts=20,joints=31,continuous_area_mm2=whole.area,
        partition_coverage_error_mm2=union_all(parts).symmetric_difference(whole).area,
        seam_centres_angles_and_keys_unchanged=True,visible_seam_gap_mm=.075,
        maximum_mask_overlap_inside_frame_mm2=overlap)

def main():
    cad=CAD.read_text();masks,domains,proof=partition_shapes(cad)
    for prefix,shapes in [('frame_mask',masks),('frame_joint_domain',domains)]:
        for i,shape in enumerate(shapes):
            name=f'{prefix}_{i}'
            # These modules use finished millimetres, unlike artwork modules.
            body=serialize(name,affinity.scale(shape,.75,.75,origin=(0,0)))
            cad,n=re.subn(r'module '+name+r'\(\) \{.*?\n\}',lambda _:body,cad,count=1,flags=re.S)
            assert n==1
    CAD.write_text(cad)
    proof['source_cad_sha256']=digest(CAD)
    (REVIEW/'partition-rebuild.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
