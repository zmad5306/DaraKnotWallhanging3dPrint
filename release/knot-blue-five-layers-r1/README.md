# Five-layer blue knot trim

The user requested two additional blue layers to provide more material for
sanding. The ten blue color modifiers extend downward by 0.40 mm, from nominal
Z12.9 to Z12.5, while the show face remains at Z13.5. Blue depth is now **1.00 mm**
instead of 0.60 mm. Their XY outlines and original upper side/top faces are
preserved; F1's intermediate-height intersections are retained by adding a
vertical extension below its old bottom rather than stretching the old sides.

All other mesh XML, object/volume settings, global settings, support paint and
actual bed poses are unchanged. The brown texture, original monotonic-line white
finish and flush blue/white show face are retained. All 50 screw reinforcement
modifiers still end at Z12.4 beneath the five continuous solid top layers.
The ten blue companion STLs are synchronized; `Knot.scad` retains its existing
references. All other project, CAD and STL files are protected by hashes.

Validation requires five blue extrusion layers at Z12.8, 13.0, 13.2, 13.4 and
13.6 on every plate. It compares brown fill, white fill below Z12.6, show-face
fill and fill above the face against the source at native G-code precision.
Native white fill at Z12.6 changes beneath the newly colored layers. Native
seam starts can move along unchanged perimeters; the resulting centerline
coverage differences are recorded separately and bounded below 0.05 mm. This
wall check covers all brown layers, lower white walls, white show-face/pin walls
and the three original blue layers. Their geometry and seam settings are unchanged.
Blue centerlines must remain within
the color region. Extrusions must cross each former screw-modifier boundary
on all five skin layers. Native round-trip geometry, unchanged settings,
G-code checksums, printable bounds, tower clearance, warnings and final native
reopen are checked. The root release audit also checks the new blue depth.

- `provenance.json`: exact source hash, ten blue-volume changes and protected files.
- `geometry.json`: unchanged upper sections, watertight blue meshes and native round trip.
- `validation.json`: final project hash, actual five-layer checks, preserved path
  signatures, screw-skin continuity and time/material estimates.
- `native-result.json`: successful native slicer result for all ten plates.

The starting file is the restored screw-skin release, SHA-256
`8a76b70a1c1430d74a16ec06c9689827d33f3902afb1d7de90e4436072c251c3`.
Earlier reports under `../knot-reinforcement-skin-r1/` and
`../knot-white-hilbert-removal-r2/` identify that source revision. The Hilbert
finish remains withdrawn. Reproduction uses `scripts/deepen_knot_blue_trim.py`
with sequential `build`, `slice`, `validate` and `publish` actions against the
recorded source hash.

Digital checks do not establish how much material can safely be sanded away
in practice. Sanding behavior and finished appearance remain physically
unqualified. No printer job was sent.

Native estimates for all ten plates are **81h 01m and 2278.10 g**, approximately
29 minutes and 6.59 g more than the three-layer blue source. These are slicer
estimates, not measured print results.

All ten native slices passed these checks with no saved warnings. The final
project reopened successfully in Bambu Studio, and the release audit passed
for all seven projects and 30 plates. All ten exported blue STL meshes are
watertight and 1.00 mm deep. The largest bounded perimeter-coverage difference
from native seam placement is 0.03542 mm.

Current `Knot.3mf` SHA-256:
`1d5fb586b295c3778cf7f6b487c98e74736eb40a28ac2c6d4ea43e4f1327cedf`.
