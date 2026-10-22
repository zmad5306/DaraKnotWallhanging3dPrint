PHYSICAL UPDATE, 2026-10-22: USER REPORTED SUCCESS.
See PHYSICAL-RESULT.txt. The test files below are retained byte-for-byte.
The following preparation notes record the original, pre-print assessment.

DARA A2L PHOTO CURVE - INFILL FIRST - r3
CURRENT TEST: Dara-A2L-Photo-Curve-Infill-First-r3.3mf
SHA-256: 5fc8fe29ea2993bdceaf690744506bd14bf757982a76b6937e9e7ce4b9192bb0
Open AS A PROJECT in Bambu Studio. A2L / 0.4 mm nozzle / Textured PEI Plate.
One complete curved photo-lip cutaway, approximately 150.45 x 141.58 x 4.0 mm.
White filament, slot 1. Estimate 35 min 30 sec, 11.55 g including supports.

WHY THIS TEST
On 2026-10-22 the user reported continuing failure on all previous tests,
including a locally changed standard-support variant, and confirmed that the
curved model perimeter pulls inward while the support stays intact. The local
standard-support project has not been inspected. The reported failure is not
support collapse. R2 did not establish a successful spacing fix.
R2's first curved wall prints before the bridge fill. In this r3 test, Print
infill first changes from OFF to ON. Native G-code confirms bridge fill is
already printed when the long curved wall starts. That gives it potential
lateral contact; adhesion remains a hypothesis requiring a physical result.
Official explanation of this setting (OrcaSlicer; Bambu behavior checked here
directly by native slicing):
https://github.com/OrcaSlicer/OrcaSlicer/wiki/quality_settings_wall_and_surfaces#print-infill-first

ONLY EXPERIMENTAL CHANGE FROM THE R2 RIGHT-HAND PIECE
is_infill_first = 0 -> 1. Wall sequence remains inner wall/outer wall.
Support top interface spacing stays 0.2 mm; two interface layers; top Z gap
stays 0.20 mm. Tree supports are retained from the inspected saved r2 project.
Same entire curve, same 4 mm height, same 2.4 mm recess, same pilot holes and
local screw reinforcement, same orientation and position. The second piece
has been removed to avoid repeating the failed control. The shorter layer
time from printing one object is a practical difference from the paired test.

UNCHANGED PROCESS
8% gyroid, 0.20 mm initial/regular layers, four walls, five top/bottom layers.
Existing screw modifiers remain 100%. White/wood/copper/blue slots and all
filament profiles remain; only white occurs inside the shallow crop.
Bridge 50 mm/s, overhang wall 10 mm/s. Temperature, cooling, flow, brim,
support type, support gaps, purge and other process settings are unchanged.
This test changes model fill order, not support speed or sparse infill density.
Infill-first applies throughout this small test; it has not been promoted to
production, where any effect on finish would need review.

OBSERVE
At layer 13 / Z2.6 mm, verify the short bridge-fill strokes print before the
long curved wall. Watch whether that wall stays curved instead of pulling
across the opening. Photograph it before later layers obscure the result.
Then compare support removal and the underside after cooling. Do not treat
this unprinted revision as a proven correction. No printer job was sent.

PROVENANCE / CHECKS
Production source: C:\Users\Zach\Repos\Personal\DaraKnotWallhanging3dPrint\Dara.3mf
Production SHA-256: 64cd3a8d9a07f55028201c68f8c48ef1ad1fdcf32d4391811a3b5ab7eded5f13
Source plate 2, F2 object 22. Uses the exact r2 right-hand crop and modifiers.
R2 source editable SHA-256: b025ccb647e3ad08151e8468ecb59e12d3bef645481f7f4478f388577e7cbd0d
Exact XY crop in crop-boundary.geojson; Z0..4.0 mm. Whole curved edge plus short
ends retained (214.17 mm). The crop's production definitions and individual
volume provenance are copied into validation.json.
Full effective global/object/volume settings compared; locked settings checked
in editable, native-sliced project and G-code. Mesh/pose unchanged within
0.001 mm; native bed bounds, support roof height, 0.20 mm air gap, white-only
extrusion, final height, actual speeds and fill-before-wall order checked.
G-code MD5 checksum verified. Only traditional-timelapse compatibility notices
are allowed; no collision or floating-region warnings. Production/A1 hashes
are unchanged. No GUI reopen or physical adhesion qualification was performed.

FILES
Dara-A2L-Photo-Curve-Infill-First-r3.3mf: current native-sliced test.
Dara-A2L-Photo-Curve-Infill-First-r3-Editable.3mf: matching editable source for the same test.
validation.json, crop-boundary.geojson, print-order-preview.png, SHA256SUMS.txt.
Historical local builder: scripts/build_photo_curve_infill_first.py.
The saved editable 3MF is the retained reproduction source; the historical
builder and failed r1/r2 experiments are not part of this release.
