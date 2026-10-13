"""Write current revision notes from the matching published audit results."""
import json,re
from validate_print_project import ROOT,PACKAGE,digest,CAD

def main():
    review=ROOT/'working/review/clean-edges'
    read=lambda p:json.loads(p.read_text())
    base=read(PACKAGE/'project-validation.json');audit=read(PACKAGE/'final-review.json')
    edge=read(review/'perimeter-review.json');mesh=read(review/'mesh-edge-review.json');geom=read(review/'cad-rebuild.json')
    assert base['clean_edges']['perimeter_review_passed'] and audit['source_sha256']==digest(CAD)
    s=audit['summary'];es=edge['summary'];plates=audit['plates']
    duration=lambda sec:f'{int(sec)//3600} h {int(sec)%3600//60} min'
    dims=next(p for p in base['test_plate']['parts'] if p['plate']==30)['dimensions_mm']
    dims_text=' x '.join(f'{v:.2f}' for v in dims)
    production_weight=sum(p['weight_g'] for p in plates[:29]);production_time=sum(p['estimated_seconds'] for p in plates[:29])
    estimates=f"Production plates 1-29: **{production_weight:,.2f} g; {duration(production_time)}**. Plate 30: **{plates[29]['weight_g']:.2f} g; {duration(plates[29]['estimated_seconds'])}**. Plate 31: **{plates[30]['weight_g']:.2f} g; {duration(plates[30]['estimated_seconds'])}**. Total: **{s['total_weight_g']:,.2f} g; {duration(s['total_estimated_seconds'])}**. These are slicer estimates."
    checks=f'''- All 39 production STLs and both material test meshes are valid solids with matching source hashes.
- All 70 assembly pieces pass the interference check; maximum numerical overlap is {audit['assembly']['maximum_overlap_mm3']:.6f} mm3 (tolerance 0.01 mm3).
- Every frame, M and backer perimeter was compared with its CAD boundary: 34 parts, maximum boundary error {mesh['maximum_boundary_error_mm']:.6f} mm.
- All 26 canonical outline loops and 320 line/arc primitives have tangent joins; maximum chord approximation is {geom['max_chord_error_mm']:.6f} mm.
- Saved white/blue perimeter paths cover all 56 large circular arcs on all 20 frame plates: {es['perimeter_arcs_checked']:,} arcs checked, maximum radial error {es['max_radial_error_mm']:.6f} mm (limit 0.06 mm).
- All 63 blue-bearing layers pass the blue-mask and white-intrusion checks. The white diamonds in Preview are seam markers, separate from extrusion paths.
- All 41 normal project meshes match the STLs within 0.0001 mm; 74 reinforcement, 21 wood and 21 blue modifiers pass validation.
- All 31 plates were re-sliced: {s['extrusion_moves_checked']:,} extrusion moves checked, minimum bed-edge clearance {s['minimum_edge_clearance_mm']:.3f} mm, including bead widths, brim/support and towers. Custom printer purge/wipe/parking routines are excluded.
'''
    description='''The complete frame artwork has been rebuilt from tangent straight lines and circular arcs. The earlier repair removed sharp local bends but missed broad waves. All 26 boundary loops are now reconstructed; the 31 lap trimming domains and 20 section masks are regenerated from the same continuous geometry, so the old traced edges cannot clip the cleaned curves. Fabric boundaries, blue offsets, eight photo openings and matching backers follow the same source.

The largest outline movement is 1.461 mm at a formerly irregular small corner. Small artwork corners use 1.5 mm fillets; overall bounds remain 914.4 x 914.4 mm. Every frame STL and all eight backers were regenerated. The six M, four wall-block and one retainer STL files are byte-identical to the preceding revision. Tested lap/key profiles, seam transforms, screw features, mounting interfaces, saved placements and slicer settings are preserved. Rabbets remain 2.4 mm deep, backers 1.6 mm thick, with 0.3 mm edge clearance.

The color-mask calculation also uses direct intersections with the original STL triangles. The previous 3D slicing helper could introduce a false triangular notch at an oblique weave seam. A regression check covers that location, and all wood/blue modifiers are regenerated with the corrected method. Solid-change verification checks every distinct vertex-height interval directly, avoiding the same coplanar Boolean artifact.
'''
    rebuild='''On a fresh delivered copy, first run `python scripts/prepare_clean_revision.py` to preserve the matching starting files. It refuses to overwrite existing revision evidence. Install numpy, shapely, trimesh, manifold3d and matplotlib for the Python tools; scipy is needed only for refitting. OpenSCAD is required for native exports.

```powershell
python scripts/rebuild_clean_cad.py
python scripts/rebuild_clean_partitions.py
python scripts/export_jointed_stls.py --jobs 3
python scripts/refresh_clean_project.py
python scripts/audit_clean_mesh_edges.py
```

The canonical `working/geometry/clean-frame-primitives.json` is portable and does not require refitting. `fit_clean_outlines.py` documents the original fitting method and requires the retained historical source; it is not needed for replay. The project refresh compares against a preserved baseline under `.work/edge-quality` and retains all existing settings. Before a new revision, preserve its starting CAD, 3MF, validation JSON and STLs there; never substitute an unrelated project.

Open the staged `clean-edges.3mf` in Bambu Studio, save models as `models.3mf`, Slice all 31 plates, then Export all sliced file as `models.gcode.3mf`. Combine them with `combine_ams_slices.py`. Run the full geometry/toolpath audit, cosmetic/color audit and `review_clean_edges.py` against that same candidate and baseline. `publish_clean_project.py` refuses publication without matching passing hashes and coverage. Refresh the part map and package only after publication.
'''
    (review/'README.md').write_text(f'''# Complete edge reconstruction - 2026-10-13

{description}
## Verified results

{checks}
The before-project measurement on plates 1 and 2 found radial deviations up to 0.373 mm. The current test measures gradual deviation from the canonical circle, rather than relying only on the former isolated-angle threshold.

## Evidence

- [All 26 outline comparisons](outline-comparison.png), [full M outline](letter-outline.png), [current color map](assembly-color-map.png).
- [CAD joins and chord errors](cad-rebuild.json), [section partition proof](partition-rebuild.json), [solid changes and unchanged interfaces](geometry-verification.json).
- [Every frame/M/backer mesh perimeter](mesh-edge-review.json), [saved circular perimeter paths](perimeter-review.json), [before measurement](before-perimeter-review.json).
- [Full 31-plate integrity audit](integrity-review.json), [63-layer color audit](after/review.json).
- [Plate 1 saved toolpaths](after/plate-01-surface.png), [plate 2](after/plate-02-surface.png). `after/plate-03-surface.png` through `after/plate-20-surface.png` and plate 30 cover the other frame surfaces; C01-C12 show the original reported defect neighborhoods.

Project SHA-256: `{audit['project_sha256']}`

CAD SHA-256: `{audit['source_sha256']}`

These checks cover digital geometry and saved slices. Plate 30 remains the physical surface/color test. The revised photo clearance and assembled load rating have not been physically verified. No printer job was sent.

## Rebuilding

{rebuild}''',encoding='utf-8')
    package_text=f'''# Complete A1 print project - clean curves

[Dara-Photo-Frame-A1-Complete.3mf](Dara-Photo-Frame-A1-Complete.3mf) contains the corrected native models and fresh saved slices for **72 pieces on 31 plates**. This supersedes the earlier local curve repair. Use Git LFS after cloning to retrieve the binary files.

{description}
| Plates | Contents |
| --- | --- |
| 01-20 | F1-F20, one frame section per plate |
| 21-26 | M1-M6, one copper section per plate |
| 27 | Backer1, Backer3, Backer5, Backer7 |
| 28 | Backer2, Backer4, Backer6, Backer8 |
| 29 | B1-B4 and 32 retainers |
| 30 | White/wood/blue weave and edge sample |
| 31 | Copper M sample |

[Part and plate map](../../../output/pdf/Dara-Part-and-Plate-Map.pdf). [Assembly guide](PRINT-READINESS.md). [Full edge review](../../review/clean-edges/README.md).

## Saved geometry and settings

The 3MF retains all colors and modifiers. STL files contain geometry only. Slot order: **1 white Generic PLA / 2 wood tan Generic PLA / 3 copper Generic PLA Silk / 4 Azurite blue Generic PLA**. Match these to the loaded AMS Lite spools.

A1, 0.4 mm nozzle, textured plate, 0.2 mm layers, four walls, 15% gyroid, with 74 local solid screw/mounting zones. Nozzle 220 C; white/wood/blue plates use a 65 C bed, copper plates 55 C. Copper outer walls/top surfaces use 40 mm/s; copper/blue flow is limited to 7.5 mm3/s. Rear-down placements and scale are retained. Backers use no brim/support; tight frame/M plates retain the 1 mm brim. Flushing into models is disabled.

The weave has 3.3 x 1.5 mm crossing pads, raised 0.3 mm above the 0.6 mm grid. Wood modifiers follow the actual relief at Z=8.4-9.9 mm, layers 43-50. The flush blue line is 1.5 mm wide with a 1.25 mm white land from the weave; its modifier is Z=12.9-13.5 mm, sliced on layers 66-68 at heights 13.2/13.4/13.6 mm. Wood and blue do not share a layer. Blue-to-white flush remains 650 mm3.

There are 11 filament changes per ordinary frame/test plate, or 12 on sections with taller white locating pins. Plate 31 is copper only. The color modifiers have been rebuilt from the clean continuous outline before section clipping; they do not follow manufacturing seams.

## Saved-file checks

{checks}
| Material | All 31 plates, including support/purge |
| --- | ---: |
'''
    package_text+='\n'.join(f'| {name} | {mass:,.2f} g |' for name,mass in zip(['White','Wood tan','Copper silk','Azurite blue'],s['filament_weights_g']))
    package_text+=f'\n\n{estimates}\n\n[project-validation.json](project-validation.json) records settings, placement and slice provenance. [final-review.json](final-review.json) is the independent audit. Plate 30 ({dims_text} mm) is the physical finish/purge test. The digital pass is not a physical print result. If Bambu asks to regenerate Preview, use Slice all with the saved settings.\n\n## Rebuilding\n\nSee the [complete edge rebuild sequence](../../review/clean-edges/README.md#rebuilding). Historical weave/rabbet/local-repair scripts describe earlier revisions.\n'
    (PACKAGE/'README.md').write_text(package_text,encoding='utf-8')
    path=PACKAGE/'PRINT-READINESS.md';old=path.read_text();assembly=old.split('## Assembly supplies and order',1)[1].split('## Recheck',1)[0]
    path.write_text(f'''# Print review - clean curves - 2026-10-13

Use [Dara-Photo-Frame-A1-Complete.3mf](Dara-Photo-Frame-A1-Complete.3mf). All frame edges, native clipping masks, blue boundaries and backers are rebuilt together and every plate has fresh slices. The [complete review](../../review/clean-edges/README.md) replaces the earlier local-bend assessment.

{description}
Plate **30** is the **{dims_text} mm** white/wood/blue sample. Inspect the crossing detail, smooth edges, blue opacity and clean white beside the blue. Plate **31** is the copper M sample. The earlier hardware/lap tests were printed; the revised 2.4 mm photo clearance and these surface tests do not yet have recorded physical results.

## Saved-file checks

{checks}
{estimates}

## Assembly supplies and order{assembly}
## Recheck

```powershell
python -m unittest discover -s scripts -p 'test_*.py'
python scripts/audit_clean_mesh_edges.py
python scripts/validate_print_project.py
python scripts/review_curve_artifacts.py --output working/review/clean-edges/after --repaired-findings working/review/curve-artifacts/review.json
python scripts/review_clean_edges.py --project working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf --baseline working/bambu/Dara-Photo-Frame-A1-Jointed/project-validation.json
```
''',encoding='utf-8')
    path=ROOT/'README.md';text=path.read_text()
    marker='**Curve repairs complete:' if '**Curve repairs complete:' in text else '**Complete edge reconstruction:'
    a=text.index(marker);b=text.index('The [final print review',a)
    text=text[:a]+'''**Complete edge reconstruction:** the frame now uses tangent lines and circular arcs throughout, including regenerated section clipping and joint endpoints. Both working CAD files, all frame/backer STLs, color modifiers and all 31 Bambu slices are synchronized. The earlier local repair missed gradual waves; the [new complete review](working/review/clean-edges/README.md) measures the saved perimeter paths as well as the CAD and meshes.

Use the current [manufacturing CAD](working/Dara-Photo-Frame-A1-Jointed.scad), [continuous clean artwork](working/Dara-Clean-Artwork.scad) and [SVG](working/Dara-Clean-Artwork.svg). Historical files under `reference/` document the original traced design and are not current production geometry. Plate 30 remains the physical finish/color check.

'''+text[b:]
    text=text.replace('68.45 x 24 mm',' x '.join(f'{v:.2f}' for v in dims[:2])+' mm').replace('The knot retains its original outline','The knot uses the reconstructed continuous outline')
    text=text.replace('The clean reference remains unchanged.', 'Both working models now use the reconstructed clean outlines. The historical reference remains archived.')
    text=text.replace('Artwork, backers, lap joints, and M attachments are preserved.', 'Lap profiles and M attachments are preserved; artwork and backers use the corrected outlines.')
    text=text.replace('The clean design reference is [reference/Dara-Clean-Reference.scad](reference/Dara-Clean-Reference.scad).\nUse this as the visual baseline for future work.', 'The historical design reference is [reference/Dara-Clean-Reference.scad](reference/Dara-Clean-Reference.scad).\nIt retains the original traced curves for provenance. Use [the reconstructed artwork](working/Dara-Clean-Artwork.scad) as the current visual baseline.')
    text=text.replace('This is the design target,\nbefore decisions about print segmentation and construction.', 'This records the earlier design target,\nbefore production segmentation and the complete curve reconstruction.')
    path.write_text(text,encoding='utf-8')
    path=ROOT/'working/stl/Dara-Photo-Frame-A1-Jointed/README.md';text=path.read_text().replace('M and accessory STLs are unchanged.','M, wall-block and retainer STLs are unchanged. All eight photo backers follow the new clean opening boundaries.')
    text=re.sub(r'^# Individual jointed-frame STL exports(?: - clean curves)?$', '# Individual jointed-frame STL exports - clean curves', text, flags=re.M)
    path.write_text(text,encoding='utf-8')
    for rel in ['working/review/curve-repair/README.md','reference/README.md']:
        path=ROOT/rel;text=path.read_text()
        banner='> Historical reference: superseded by the complete clean-edge reconstruction in working/review/clean-edges. The original traced geometry and local repair are retained as history, not current production evidence.\n\n'
        if not text.startswith('> Historical reference:'):path.write_text(banner+text,encoding='utf-8')
    path=ROOT/'working/stl/Dara-Print-Checks/README.md';text=path.read_text()
    text=re.sub(r'\| 30 \| Test-Weave-Full-Width \|[^\n]+',f"| 30 | Test-Weave-Full-Width | White/wood/Azurite blue Generic PLA; 65 C bed | {plates[29]['weight_g']:.2f} g; {duration(plates[29]['estimated_seconds'])} |",text)
    text=re.sub(r'\| 31 \| Test-M-Letter \|[^\n]+',f"| 31 | Test-M-Letter | Copper Generic PLA Silk; 55 C bed | {plates[30]['weight_g']:.2f} g; {duration(plates[30]['estimated_seconds'])} |",text)
    text=re.sub(r'\*\*68\.45 mm wide x 24 mm long x 13\.5 mm high\*\*',f'**{dims_text} mm**',text)
    text=text.replace('cropped from the restored F7 mesh','cropped from the clean reconstructed F7 mesh')
    path.write_text(text,encoding='utf-8')
    print('Current documentation updated from matching audited artifacts.')

if __name__=='__main__':main()
