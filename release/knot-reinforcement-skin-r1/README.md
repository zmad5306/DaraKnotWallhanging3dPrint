# Knot screw reinforcement: continuous top skin

The user reported visible circular boundaries on the finished knot above the
screw reinforcement. The saved project had 50 cylindrical 100% infill modifiers
extending from Z0 to Z17, through the nominal Z13.5 show face. Their regions split
the native top-surface paths.

The current root `Knot.3mf` ends those modifiers at Z12.4. Their XY outlines,
bottoms and 100% infill settings are unchanged. The 1.1 mm nominal clearance lets
the existing five top shell layers print continuously across the old circular
boundaries. Actual screw holes, body geometry, material boundaries, support
paint, bed poses and all project/object/volume process settings are preserved.
The structural bodies remain 8% gyroid, 0.20 mm layers, four walls and five
top/bottom layers on the A2L with its 0.4 mm nozzle. Infill-first and the approved
0.2 mm support interface spacing remain in place.

All ten plates were resliced in Bambu Studio 02.08.02.61. Validation checks all
50 reinforcement locations for extrusion crossing the former cylinder boundary
on each of the five skin layers, Z12.8/13.0/13.2/13.4/13.6. It also compares
normal and color mesh XML byte-for-byte, modifier topology/XY/bottom coordinates,
all settings, support paint, bed poses, native round-trip geometry, G-code
configuration and checksums, filament heights, finish directions, bed bounds,
startup tower and actual tower clearance. The saved final project is reopened
natively. The ten saved slices report no warnings.

- `provenance.json`: exact input path/hash, editable hash and 50 modifier changes.
- `geometry.json`: local show-face height checks and unchanged geometry/settings.
- `validation.json`: final hash, per-location toolpath checks, preservation,
  native reopen and per-plate estimates.
- `native-result.json`: native slicer result for all ten plates.
- `top-surface-before-after.png`: actual old/new native top-layer extrusion on
  plate 3; the dashed circle marks the former modifier boundary.

The matching 50 modifier STL files are updated in `Knot STL/`; `Knot.scad`
continues to reference them with its existing transforms. All other projects
remain unchanged by this correction. The release catalog and stored G-code
hashes identify the current root file. Total slicer estimate: **80h 32m,
2271.52 g**. No printer job was sent.

Digital verification does not qualify the physical finish. A print of this
revision is still required to confirm that the visible circles are gone.

Reproduction uses `scripts/correct_knot_reinforcement_skin.py` against the exact
source hash recorded in provenance. Its `build`, `slice`, `validate` and
`publish` actions are sequential; validation must succeed before publication.
