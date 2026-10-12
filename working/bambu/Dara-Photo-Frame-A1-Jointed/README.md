# Complete A1 print project

[Dara-Photo-Frame-A1-Complete.3mf](Dara-Photo-Frame-A1-Complete.3mf) contains one
complete assembly: 39 distinct STL parts and 70 printed pieces across 29 plates.
It includes editable models, local infill modifiers, plate thumbnails, and sliced
toolpaths. The file is stored with Git LFS; run `git lfs pull` after cloning.

The [four-page part and plate map](../../../output/pdf/Dara-Part-and-Plate-Map.pdf)
shows frame and M assembly positions, backer and wall-block locations, and the
three shared plate layouts. Assembly maps all use the same front-view orientation.

| Plates | Parts | Quantity |
| --- | --- | --- |
| 01-20 | F1-F20 | One section per matching plate |
| 21-26 | M1-M6 | One section per plate, in order |
| 27 | Backer1, Backer3, Backer5, Backer7 | One each |
| 28 | Backer2, Backer4, Backer6, Backer8 | One each |
| 29 | B1-B4 and Retainer | One of each block and 32 retainers |

## Print settings

- Bambu Lab A1, 0.4 mm nozzle, Generic PLA, textured PEI plate, 0.2 mm layers.
- Four wall loops and 15% gyroid infill for the body.
- Local 100% infill around M screw seats and pilots, photo-tab screws, wall-block
  screws, wall keyhole seats, and retainer screw seats. The lap tongues and roots
  use the normal body settings, following the tested joint reference.
- All parts keep their original scale and rear-down print orientations.
- Backers print four per plate, by layer, with no brim or supports. Their minimum
  spacing is about 1.8 mm, with a 1.5 mm model clearance from the bed edge.
- The tightest frame and M plates use a 1 mm brim and zero additional support-base
  expansion to keep their generated toolpaths on the bed.

The supplied project was sliced in Bambu Studio 02.08.02.61. All 29 plates finished
without slicer warnings. Extrusion paths, including support and brim widths, stay
inside the 256 mm bed; the minimum checked edge clearance is 0.826 mm. Estimated
use is 3.254 kg of PLA and 111.7 hours over all plates. These are slicer estimates.

[project-validation.json](project-validation.json) records the final project hash,
part quantities and source hashes, placements, modifiers, per-plate estimates,
toolpath bounds, and the geometry comparison after Bambu Studio re-export. All
normal meshes match the source STLs within 0.0001 mm. Purchased screws and
reference M washers are not printed parts.

## Rebuilding

`python scripts/build_jointed_bambu_project.py`, run from the repository root,
creates the initial **unsliced** 3MF and layout report from the validated STL set
and tracked joint-test preset. It replaces the output project and report. The
supplied sliced project was subsequently exported and verified in Bambu Studio.
Re-slice and refresh validation before replacing that published artifact.

The PDF uses the saved project's actual object-to-plate mapping, checked against
the validation report, and projects the source meshes into their CAD assembly
positions. To regenerate it from the validated project:

```powershell
python scripts/build_part_layout_map.py prepare
python scripts/build_part_layout_map.py render
```

The prepare stage needs numpy, shapely, and trimesh. The render stage needs
reportlab and can run with a separate Python interpreter. Intermediate map data
goes in ignored `.work/part-layout-map/`; the final PDF goes in `output/pdf/`.
