"""Compare every frame, M and backer perimeter to its native CAD boundary."""
import json
from validate_print_project import ROOT,CAD,STLS,digest
from add_blue_ribbon_edge import artwork,in_print_coordinates
from build_jointed_bambu_project import read_array
from refresh_curve_project import solid
from review_curve_artifacts import shape_from_section
from mesh_sections import mesh_slice
from shapely import affinity
from shapely.geometry import Point
import trimesh

def main():
    cad=CAD.read_text();records=[]
    for family,prefix,count,z,outline in [('frame','F',20,13.4,'knot_outline'),('M','M',6,10.4,'letter_outline')]:
        placements=read_array(cad,family+'_placements');whole=artwork(cad,outline)
        for i in range(count):
            name=f'{prefix}{i+1}';path=STLS/(name+'.stl')
            mask=affinity.scale(artwork(cad,f'{family}_mask_{i}'),1/.75,1/.75,origin=(0,0))
            expected=whole.intersection(mask)
            if family=='frame':
                for mount in read_array(cad,'screw_mounts'):
                    if mount[1]==i:expected=expected.difference(Point(mount[2]).buffer(2,quad_segs=16))
            expected=in_print_coordinates(expected,placements[i])
            actual=mesh_slice(trimesh.load_mesh(path),z)
            error=actual.boundary.hausdorff_distance(expected.boundary)
            area=actual.symmetric_difference(expected).area
            # STL roundoff and native CSG polygon quantization only.
            # Integrated area roundoff grows with perimeter length. Bound it
            # by a 0.05-micron strip, in addition to the independent Hausdorff limit.
            assert error<.0001 and area<expected.length*.00005,(name,error,area)
            records.append(dict(part=name,z_mm=z,max_boundary_error_mm=error,symmetric_area_error_mm2=area,stl_sha256=digest(path)))
    for i,center in enumerate(read_array(cad,'photo_centres'),1):
        path=STLS/f'Backer{i}.stl'
        expected=affinity.translate(artwork(cad,f'photo_loop_{i}').buffer(3.7,join_style=2),-center[0]*.75,-center[1]*.75)
        actual=mesh_slice(trimesh.load_mesh(path),.8)
        error=actual.boundary.hausdorff_distance(expected.boundary);area=actual.symmetric_difference(expected).area
        assert error<.0001 and area<expected.length*.00005,(i,error,area)
        records.append(dict(part=f'Backer{i}',z_mm=.8,max_boundary_error_mm=error,symmetric_area_error_mm2=area,stl_sha256=digest(path)))
    report=dict(source_cad_sha256=digest(CAD),all_passed=True,parts_checked=len(records),
        maximum_boundary_error_mm=max(r['max_boundary_error_mm'] for r in records),parts=records,
        unchanged_hardware='B1-B4 and Retainer are checked for byte identity, valid solids and assembly fit in the geometry/integrity audits.')
    (ROOT/'working/review/clean-edges/mesh-edge-review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='parts'},indent=2))

if __name__=='__main__':main()
