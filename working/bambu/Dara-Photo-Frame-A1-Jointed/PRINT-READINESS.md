# Print review - 2026-10-13

**The revised project passes the digital audit.** The user has printed the earlier hardware and lap tests and reports that the backer left insufficient photo room, possibly due to support roughness. The preceding clearance revision deepened the rabbet from **2.0 to 2.4 mm**. With the existing 1.6 mm backer, 0.8 mm remains for the photo and surface clearance. Physical fit remains unverified. This color revision adds a flush 1.5 mm Azurite blue edge thread to the white ribbon, preserving that geometry.

Use [Dara-Photo-Frame-A1-Complete.3mf](Dara-Photo-Frame-A1-Complete.3mf). Plate **30** contains only the **68.45 x 24 x 13.5 mm** white/wood/blue sample from F7. Plate **31** contains only **Test-M-Letter**, with the copper Generic PLA Silk profile and 55 C bed. The optional standalone [photo-frame fit coupon](../../stl/Dara-Print-Checks/Test-Photo-Frame.stl) also has the deeper recess; the material test plates remain unchanged in purpose.

The alternating 0.3 mm weave crossing pads are preserved. The [rabbet comparison](../../review/rabbet-clearance/geometry-verification.json) verifies all 20 frame sections: only the recess depth changes, with geometry outside Z=2.0-2.4 mm unchanged within numerical tolerance. The M, backer, wall-block and retainer STL files are byte-identical to the preceding revision. Production placements and saved material settings are retained.

## Saved-file checks

- All 39 production STLs and two test meshes are valid solids; the current CAD hash and STL hashes match their manifests.
- All 70 production pieces were checked in their assembled positions, including lap order and mating interfaces.
- All 41 normal meshes in the 3MF match their source geometry within 0.0001 mm. The 74 reinforcement modifiers, 21 wood modifiers and 21 blue modifiers were checked. Blue paths were compared with the continuous CAD edge offsets.
- Wood occupies layers 43-50 on the frame and short test, with eight wood/white color changes. Blue occupies layers 66-68 only, after the wood is complete. Total changes are 11 per frame/test plate, or 12 where taller white M locating pins require a final return to white. Plate 31 uses copper only, with no filament changes and a 55 C bed throughout printing; plate 30 uses a 65 C bed.
- All 31 saved toolpaths pass the extrusion-bounds audit: 7,356,694 checked moves and 0.673 mm minimum bed-edge clearance. Printer purge/wipe/parking routines are outside that model-path check.
- Estimated production use: 3,402.99 g and 126 h 57 min. Weave test: 18.44 g and 0 h 59 min. Copper test: 23.28 g and 1 h 10 min.

The matching report is [final-review.json](final-review.json). Inspect the weave sample for crossing detail, both blue edge lines, clean white beside the blue, and surface finish. Map slot 4 to the Azurite spool. The lines finish flush with the white rails; no assembly of separate thread inserts is needed. The separate copper sample checks the silk finish using the same settings as the M plates. The digital review does not record physical print results for these revised samples.

## Assembly supplies and order

| Purchased item | Quantity | Use |
| --- | --- | --- |
| Selected #6-19 x 1/2-inch pan-head plastic thread-forming screws | 50 | 32 tabs + 8 wall-block screws + 10 M screws |
| 10 mm OD x 4 mm ID x 1 mm washers | 10 | M screws only |
| Wall fasteners/anchors or strips appropriate to the actual wall and load | Chosen for installation | Separate from the 50 assembly screws |
| Adhesive proven on the chosen PLA and lap sample | As required | Keyed laps require a bonded assembly |

The M screw stack provides 7.7 mm engagement, 1 mm nominal tip clearance, and
1.8 mm front cover. Photo and block screws provide 9.7 mm engagement, 1 mm tip
clearance, and 2.8 mm front cover. Different screw or washer dimensions change
these clearances.

Label parts as they leave the plate. All map positions use the front view.
Dry-fit first on a flat surface, then bond following the CAD's tongue-before-socket
order; lower each socket onto the earlier tongues:

- **Frame:** F1, F2, F8, F15, F19, F20, F3, F14, F18, F11, F17, F9, F16,
  F12, F6, F7, F13, F10, F5, F4.
- **M:** M1, M6, M2, M4, M3, M5.

After the bonded assemblies have cured, seat M on the locating pins and install
its ten screws/washers from the rear. B1/B2/B3/B4 fit F3/F5/F16/F18 respectively.
Install the backers and four tabs per photo. Verify all four wall faces seat in
one plane and the photo hardware clears the wall before mounting. A digital
pass does not establish a safe load rating for the completed hanging.

## Recheck

From the repository root, with numpy, trimesh and manifold3d available:

```powershell
python -m unittest discover -s scripts -p test_validate_print_project.py
python scripts/validate_print_project.py
```

This audits the existing saved artifacts and writes `final-review.json`; it does
not overwrite or re-slice the production 3MF. Re-export and re-slice deliberately
if physical testing requires changes to the design or process.
