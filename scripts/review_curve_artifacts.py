"""Review source curvature and saved blue/white surface toolpaths without edits.

This complements validate_print_project.py: valid solids can contain cosmetic
kinks. Candidate detection is a screening rule, not proof that a shape is smooth.
Produces reproducible JSON and plots; never rewrites the CAD/STLs/3MF.
"""
import argparse
import json
import math
from pathlib import Path
import re
import zipfile

from validate_print_project import ROOT, CAD, PACKAGE, STLS, TOKEN, digest
from add_blue_ribbon_edge import artwork, polygons, in_print_coordinates, coupon_shape
from build_jointed_bambu_project import read_array
import numpy as np
import trimesh
from shapely import affinity, points, distance
from shapely.geometry import Point, Polygon, LineString, GeometryCollection
import manifold3d
from mesh_sections import mesh_slice


def curve_candidates(shape, threshold=6):
    """Isolated turns on otherwise gentle outlines, using physical arc distance.

    Dense vertices at intentional 1.5 mm corner fillets must not create false
    positives. Exclude neighborhoods with >45 degrees absolute turn in +/-5 mm.
    All omitted sharp corners still need visual inspection of the overview.
    """
    result, count = [], 0
    for pi, poly in enumerate(polygons(shape)):
        for ri, ring in enumerate([poly.exterior, *poly.interiors]):
            xy = np.asarray(ring.coords)[:-1]
            before, after = xy - np.roll(xy, 1, axis=0), np.roll(xy, -1, axis=0) - xy
            lengths = np.linalg.norm(after, axis=1)
            assert np.all(lengths > 0)
            arclength = np.r_[0, np.cumsum(lengths)[:-1]]
            turns = np.degrees(np.arctan2(before[:, 0]*after[:, 1]-before[:, 1]*after[:, 0],
                                         (before*after).sum(axis=1)))
            count += len(xy)
            for i in np.flatnonzero(np.abs(turns) > threshold):
                ds = np.abs(arclength - arclength[i])
                ds = np.minimum(ds, lengths.sum()-ds)
                neighborhood_turn = float(np.abs(turns[ds <= 5]).sum())
                if neighborhood_turn > 45:
                    continue
                if any(np.linalg.norm(xy[i]-r['assembly_xy_mm']) < 4 for r in result):
                    continue
                # Distance from vertex to chord connecting its two neighbors.
                # This is a local kink metric, NOT a proposed repair displacement.
                chord = LineString([xy[(i-1) % len(xy)], xy[(i+1) % len(xy)]])
                result.append(dict(polygon=pi, ring=ri, vertex=int(i), assembly_xy_mm=xy[i].tolist(),
                                   turn_degrees=float(turns[i]), nearby_absolute_turn_degrees=neighborhood_turn,
                                   neighbor_chord_deviation_mm=Point(xy[i]).distance(chord)))
    return result, count


def arc_samples(start, end, values, ccw):
    """Sample XY arc with <=0.002 mm chord error; preserve exact endpoint."""
    center = np.array(start) + [values.get('I', 0), values.get('J', 0)]
    radius = np.linalg.norm(np.array(start)-center)
    assert radius > 0
    a, b = [math.atan2(q[1]-center[1], q[0]-center[0]) for q in (start, end)]
    sweep = ((b-a) if ccw else (a-b)) % (2*math.pi)
    if math.dist(start, end) < 1e-8:
        sweep = 2*math.pi
    step = min(.1, 2*math.acos(max(-1, 1-.002/radius)))
    angles = a + (1 if ccw else -1)*np.linspace(0, sweep, max(2, math.ceil(sweep/step)+1))
    xy = center + radius*np.column_stack([np.cos(angles), np.sin(angles)])
    xy[0], xy[-1] = start, end
    return xy


def surface_paths(gcode):
    """Read actual motion, retaining rail surface layers and wood final surface.

    Custom printer routines, purge towers, supports and travel aren't model paths.
    Each record has the original line number for traceability.
    """
    x = y = z = e = 0.
    relative_e = relative_xyz = False
    tool, feature, width, layer_z = None, 'Custom', .5, 0.
    selected = {10., 13.2, 13.4, 13.6}
    excluded = {'Custom', 'Prime tower', 'Support', 'Support interface', 'Brim', 'Skirt'}
    paths, model_moves, arc_moves = [], 0, 0
    for lineno, raw in enumerate(gcode.splitlines(), 1):
        if raw.startswith('; FEATURE: '):
            feature = raw.split(': ', 1)[1]
        elif raw.startswith('; LINE_WIDTH: '):
            width = float(raw.split(': ', 1)[1])
        elif raw.startswith('; Z_HEIGHT: '):
            layer_z = round(float(raw.split(': ', 1)[1]), 4)
        line = raw.split(';', 1)[0].strip()
        if not line:
            continue
        command = line.split()[0]
        if re.fullmatch(r'T[0-3]', command):
            tool = int(command[1:])+1
        elif command in ('M82', 'M83'):
            relative_e = command == 'M83'
        elif command in ('G90', 'G91'):
            relative_xyz = command == 'G91'
        elif command == 'G92':
            values = {k:float(v) for k,v in TOKEN.findall(line)}
            x,y,z,e = [values.get(k,v) for k,v in zip('XYZE',(x,y,z,e))]
        elif command in ('G0','G1','G2','G3'):
            values = {k:float(v) for k,v in TOKEN.findall(line)}
            nx,ny,nz = [v+values.get(k,0) if relative_xyz else values.get(k,v)
                        for k,v in zip('XYZ',(x,y,z))]
            de = values.get('E',0) if relative_e else values.get('E',e)-e
            moving = any(k in values for k in ('X','Y','I','J'))
            if de > 0 and moving and feature not in excluded:
                model_moves += 1
                arc_moves += command in ('G2','G3')
                if layer_z in selected:
                    if command in ('G2','G3') and 'R' in line:
                        raise ValueError('Radius-form arcs need explicit handling')
                    xy = (arc_samples((x,y),(nx,ny),values,command=='G3')
                          if command in ('G2','G3') else np.array([[x,y],[nx,ny]]))
                    paths.append(dict(xy=xy, tool=tool, feature=feature, width=width,
                                      z=layer_z, line=lineno))
            x,y,z = nx,ny,nz
            e = e+values.get('E',0) if relative_e else values.get('E',e)
    return paths, model_moves, arc_moves


def shape_from_section(section):
    # Even-odd rings retain holes regardless of orientation.
    shape = GeometryCollection()
    for ring in section.to_polygons():
        shape = shape.symmetric_difference(Polygon(ring))
    return shape


def outline(ax, shape, color, lw=1, vertices=False):
    for poly in polygons(shape):
        for ring in [poly.exterior, *poly.interiors]:
            ax.plot(*np.array(ring.coords).T, color=color, linewidth=lw,
                    marker='.' if vertices else None, markersize=2)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, default=ROOT/'working/review/curve-artifacts')
    ap.add_argument('--project', type=Path)
    ap.add_argument('--baseline', type=Path, default=PACKAGE/'project-validation.json')
    ap.add_argument('--repaired-findings', type=Path, help='Historical findings to render again for before/after comparison')
    args = ap.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    cad = CAD.read_text()
    base = json.loads(args.baseline.read_text())
    project = args.project or PACKAGE/base['project']
    assert digest(project) == base['project_sha256']
    placements = read_array(cad, 'frame_placements')
    shapes = {name:artwork(cad,name+'_outline') for name in ('knot','fabric','letter')}
    fabric = shapes['fabric'].buffer(.1125,quad_segs=16)
    blue = (fabric.buffer(2.75,quad_segs=16)-fabric.buffer(1.25,quad_segs=16)).intersection(shapes['knot']).simplify(.001)
    candidates, stats = {}, {}
    for name, shape in shapes.items():
        candidates[name], stats[name] = curve_candidates(shape)
    # Fabric records duplicate five knot boundary locations. Keep both arrays
    # in the report, but count unique physical defects from the knot outline.
    findings = candidates['knot']
    meshes = {f'F{i}':trimesh.load_mesh(STLS/f'F{i}.stl') for i in range(1,21)}
    for record in findings:
        xy = Point(record['assembly_xy_mm'])
        matches = []
        for i,p in enumerate(placements,1):
            local = in_print_coordinates(xy,p)
            mesh = meshes[f'F{i}']
            err = float(np.linalg.norm(mesh.vertices[:,:2]-np.array(local.coords)[0],axis=1).min())
            if err < .001:
                item = base['plate_layout'][i-1]['items'][0]
                matches.append(dict(plate=i,part=f'F{i}',local_xy_mm=list(local.coords)[0],
                                    plate_xy_mm=(np.array(local.coords)[0]+item['xy']).tolist(),
                                    source_vertex_error_mm=err))
        assert matches, record
        record['locations'] = matches
        record['affects_blue_edge'] = any(xy.distance(Point(c['assembly_xy_mm'])) < .01 for c in candidates['fabric'])
    findings.sort(key=lambda r:(r['locations'][0]['plate'], not r['affects_blue_edge'],r['assembly_xy_mm']))
    for i,r in enumerate(findings,1):
        r['id'] = f'C{i:02d}'
    rows=max(1,math.ceil(len(findings)/4))
    fig,axs=plt.subplots(rows,4,figsize=(16,4*rows),squeeze=False)
    for ax in axs.flat:
        ax.set_visible(False)
    if not findings:
        fig.text(.5, .5, 'No isolated curve defects detected at the stated screening threshold.',
                 ha='center', va='center', fontsize=16, color='#16759b')
    for ax,r in zip(axs.flat,findings):
        ax.set_visible(True)
        x,y=r['assembly_xy_mm']
        for shape,color in [(shapes['knot'],'#444444'),(fabric,'#b99352'),(blue,'#295d8a')]:
            outline(ax,shape,color,vertices=True)
        ax.scatter([x],[y],color='#d53832',s=18,zorder=5)
        ax.set(xlim=(x-7,x+7),ylim=(y-7,y+7),aspect='equal')
        ax.set_title(f"{r['id']} - Plate {r['locations'][0]['plate']} / {r['locations'][0]['part']}\n"
                     f"{abs(r['turn_degrees']):.1f} degree bend"+(' - blue edge' if r['affects_blue_edge'] else ' - outer edge'),fontsize=10)
        ax.grid(alpha=.18);ax.tick_params(labelsize=8)
    fig.suptitle('Source curve defects - millimetres in assembled front view',fontsize=16)
    fig.tight_layout(rect=(0,0,1,.97));fig.savefig(out/'curve-findings.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,11))
    outline(ax,shapes['knot'],'#a3a3a3',.65);outline(ax,blue,'#295d8a',.7)
    for r in findings:
        x,y=r['assembly_xy_mm'];ax.scatter([x],[y],c='#d53832',s=20)
        ax.annotate(f"{r['id']} / P{r['locations'][0]['plate']}",(x,y),xytext=(8,10),textcoords='offset points',fontsize=9)
    ax.set(xlim=(-510,530),ylim=(-490,495),aspect='equal');ax.axis('off')
    affected=sorted({l['plate'] for r in findings for l in r['locations']})
    fig.suptitle(f'Curve review - {len(findings)} locations on {len(affected)} frame plates',fontsize=16)
    fig.tight_layout();fig.savefig(out/'assembly-findings.png',dpi=180);plt.close(fig)
    reference=ROOT/'working/Dara-Clean-Artwork.scad'
    if not reference.exists():reference=ROOT/'reference/Dara-Clean-Reference.scad'
    reference_knot=artwork(reference.read_text(),'knot_outline')
    report=dict(project_sha256=digest(project),source_cad_sha256=digest(CAD),
                reference_cad_sha256=digest(reference),
                knot_difference_from_clean_reference_mm2=shapes['knot'].symmetric_difference(reference_knot).area,
                scope='Source-outline cosmetic screening, matching source STL vertices, all-plate saved motion parsing, and blue/white surface path placement.',
                screening=dict(min_isolated_turn_degrees=6,neighborhood_radius_mm=5,max_neighborhood_absolute_turn_degrees=45,
                               limitation='Smaller deviations and intentional/high-curvature corners require visual judgment; this is not a guarantee of an artifact-free physical print.'),
                outline_vertices_screened=stats,raw_candidates=candidates,findings=findings,plates=[])
    palette={1:'#888888',2:'#C2AB84',3:'#B87333',4:'#295D8A'}
    detail_findings = findings
    if args.repaired_findings:
        detail_findings = json.loads(args.repaired_findings.read_text())['findings']
    with zipfile.ZipFile(project) as archive:
        for number,layout in enumerate(base['plate_layout'],1):
            paths, moves, arcs=surface_paths(archive.read(f'Metadata/plate_{number}.gcode').decode())
            plate=dict(plate=number,name=layout['name'],model_extrusion_moves_parsed=moves,model_arcs_parsed=arcs)
            if number <=20 or number==30:
                name=layout['items'][0]['name'];origin=layout['items'][0]['xy']
                local=(in_print_coordinates(blue,placements[number-1]) if number<=20 else coupon_shape(blue,cad))
                mesh=meshes[name] if number<=20 else trimesh.load_mesh(ROOT/'working/stl/Dara-Print-Checks'/f'{name}.stl')
                body=manifold3d.Manifold(manifold3d.Mesh64(mesh.vertices,mesh.faces.astype(np.uint64)))
                footprint=mesh_slice(mesh,13.2)
                mask=affinity.translate(local.intersection(footprint),*origin)
                core=mask.buffer(-.3)
                layers=[]
                for height in (13.2,13.4,13.6):
                    bpaths=[p for p in paths if p['tool']==4 and p['z']==height]
                    wpaths=[p for p in paths if p['tool']==1 and p['z']==height]
                    assert bpaths, (number,height)
                    # Check complete line segments/arcs, not endpoints alone.
                    blue_lines=[LineString(p['xy']) for p in bpaths]
                    white_lines=[LineString(p['xy']) for p in wpaths]
                    outside=sum(line.difference(mask.buffer(.03)).length for line in blue_lines)
                    intrusion=sum(line.intersection(core).length for line in white_lines)
                    xy=np.concatenate([p['xy'] for p in bpaths])
                    max_out=float(np.max(distance(points(xy),mask)))
                    layers.append(dict(z_mm=height,blue_extrusion_moves=len(bpaths),white_extrusion_moves=len(wpaths),
                                       blue_centerline_length_outside_mask_plus_0_03_mm=outside,
                                       max_sampled_blue_centerline_outside_mm=max_out,
                                       white_centerline_length_in_blue_core_mm=intrusion))
                plate['surface_color_checks']=layers
                plate['blue_mask_regions']=len(polygons(mask))
                # Surface-only plots omit the preview's seam symbols altogether.
                fig,ax=plt.subplots(figsize=(8,8))
                for tool,zs in [(2,{10.}),(1,{13.6}),(4,{13.6})]:
                    rows=[p for p in paths if p['tool']==tool and p['z'] in zs]
                    ax.add_collection(LineCollection([p['xy'] for p in rows],colors=palette[tool],linewidths=.32))
                ax.set(xlim=(0,256),ylim=(0,256),aspect='equal');ax.set_title(f'Plate {number} / {name} - saved surface toolpaths')
                ax.set_xlabel('Bed X (mm)');ax.set_ylabel('Bed Y (mm)');ax.grid(alpha=.15)
                fig.tight_layout();fig.savefig(out/f'plate-{number:02d}-surface.png',dpi=170);plt.close(fig)
                for r in detail_findings:
                    for location in r['locations']:
                        if location['plate']!=number:continue
                        x,y=location['plate_xy_mm']
                        fig,ax=plt.subplots(figsize=(6,6))
                        for tool,zs in [(2,{10.}),(1,{13.6}),(4,{13.6})]:
                            rows=[p for p in paths if p['tool']==tool and p['z'] in zs
                                  and np.any(np.linalg.norm(p['xy']-[x,y],axis=1)<15)]
                            ax.add_collection(LineCollection([p['xy'] for p in rows],colors=palette[tool],linewidths=.85))
                        ax.set(xlim=(x-8,x+8),ylim=(y-8,y+8),aspect='equal');ax.grid(alpha=.15)
                        ax.set_title(f"{r['id']} / plate {number} - actual toolpaths\nSeam symbols omitted")
                        ax.set_xlabel('Bed X (mm)');ax.set_ylabel('Bed Y (mm)')
                        fig.tight_layout();fig.savefig(out/f"{r['id']}-toolpath.png",dpi=170);plt.close(fig)
            report['plates'].append(plate)
            print(f'Plate {number}: parsed {moves} model moves'+(f'; {plate.get("surface_color_checks")}' if 'surface_color_checks' in plate else ''),flush=True)
    color_checks = [layer for p in report['plates'] for layer in p.get('surface_color_checks', [])]
    colors_pass = len(color_checks) == 63 and all(
        c['blue_centerline_length_outside_mask_plus_0_03_mm'] < 1e-6 and
        c['white_centerline_length_in_blue_core_mm'] < 1e-6 for c in color_checks)
    report['summary']=dict(unique_curve_findings=len(findings),affected_plates=sorted({l['plate'] for r in findings for l in r['locations']}),
                           blue_edge_findings=sum(r['affects_blue_edge'] for r in findings),
                           plates_parsed=len(report['plates']),model_extrusions_parsed=sum(p['model_extrusion_moves_parsed'] for p in report['plates']),
                           blue_white_layers_checked=len(color_checks), surface_color_checks_passed=colors_pass,
                           cosmetic_review_passed=not findings and colors_pass,production_artifacts_modified=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['summary'],indent=2))


if __name__=='__main__':
    main()
