# Hardware fit and weave coupons

**Print plate 30 in the [complete Bambu project](../../bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf).**
It is named **30 - PRINT FIRST - Hardware, lap and weave tests**, contains ten
separate pieces, and is already sliced for the A1, 0.4 mm nozzle, PLA and 0.2 mm
layers. It uses four walls, 15% gyroid and nine local 100% screw/keyhole zones.
Estimated use is **204.72 g and 8 h 24 min**.
Test-M-Letter prints in copper / Generic PLA Silk. The full-width weave sample
uses white and wood / Generic PLA; the other eight pieces use white. This plate
has 59 filament changes, six more than the previous hardware-only plate.
The three small photo coupons were moved to make room for the new sample.
[plate-30-manifest.json](plate-30-manifest.json) records the ten source meshes,
their hashes, plate positions, reinforcement zones, and sliced checks.

| Named objects on plate 30 | Check |
| --- | --- |
| Test-Photo-Frame, Test-Photo-Backer, Test-Photo-Tab | Screw grip, photo/backer retention, tab rotation |
| Test-Wall-Block-B1, Test-Wall-Socket-B1 | Key fit, two recessed screws, wall keyhole and support removal |
| Test-M-Frame, Test-M-Letter | Actual F14/M5 screw stack and both locating pins, including the relieved hole |
| Test-Lap-Tongue, Test-Lap-Socket | Actual F7/F4 lap fit and bonded joint at the production infill settings |
| Test-Weave-Full-Width | Full-width white rails, recessed wood backing, and raised weave finish |

The weave sample is **68.45 mm wide x 24 mm long x 13.5 mm high**, cropped from
a straight section of the production F7 STL. Both outer rails remain intact;
only the short ends are cut. It uses the frame's actual weave geometry, four-wall /
15% gyroid profile, and wood filament modifier at Z=8.4-9.6 mm (layers 43-48).
Inspect the thread detail, recessed surface, white/wood boundary, and color
contrast before printing the frame. The sample lies near the back-left of the
plate, beside the prime tower. Its short ends are exposed cross-sections.

The updated plate uses about 14.23 g and 36 minutes more than the previous
nine-piece plate, including the additional purge. Production plates 1-29 are
unchanged. A standalone [STL](Test-Weave-Full-Width.stl) is also provided;
use the complete 3MF to preserve the two-color assignment.

The M and lap coupons are cropped directly from current production STLs. The M
pair retains its actual pin spacing and full local thickness; no surrogate boss
is used. The lap pair retains the 13.5 mm production rail depth and original
keys/pockets. Their outside cut edges are coupon boundaries, not mating features.

Use **four of the selected #6-19 x 1/2-inch screws** (one photo, two wall, one M),
**one 10 mm OD x 4 mm ID x 1 mm washer for M**, and the intended wall screw for
the keyhole check. Remove support before assembly. Align the M pair by both
pins; its cropped outlines need not coincide. Let a bonded lap sample cure
according to the adhesive instructions before assessing it.

![Ten-piece test plate model layout](../../bambu/Dara-Photo-Frame-A1-Jointed/fit-test-plate.png)

The model thumbnail shows modifier-colored areas in the base color. Use sliced
Preview's Filament view to see the wood weave assignment.

## Standalone source coupons

These are new exports of the production CAD's existing fit-sample modes at its
saved defaults. They are **unsliced STL files in millimetres**, not part of the
70-piece production assembly. [manifest.json](manifest.json) records their
source and file hashes. Every separate solid is watertight and rests at Z=0.

| File | Contents | Footprint |
| --- | --- | --- |
| [Photo-Fit-Sample.stl](Photo-Fit-Sample.stl) | Full-depth frame coupon, backer strip, rotating tab | 47 x 39 mm |
| [Wall-Fit-Sample-B1.stl](Wall-Fit-Sample-B1.stl) | B1 and a matching full-depth slot/pilot coupon | 140 x 90 mm |

Import each file at 100% scale and keep its existing flat orientation. Each file
contains separate printable solids; preserve their separation. Use the production
A1/0.4 mm nozzle/PLA/0.2 mm profile. For these small **fit-only** samples, use
100% infill to reproduce the production screw zones' solid material, and enable
normal snug supports with build-plate-only disabled. Slice and inspect the
rabbet, blind-hole roofs, and enclosed keyhole channel before printing. Remove
supports before testing. These coupons do not establish production joint strength.

Use the selected #6-19 x 1/2-inch plastic thread-forming screws. The photo tab
should hold the backer and actual photo stack, rotate clear after slight loosening,
and snug without splitting the pilot. B1's keys should fully seat in its matching
coupon, both screws should snug with recessed heads, and the intended wall screw
should enter the keyhole, slide into its upper seat, and release again.

For the actual M screw and paired locator fit, print **F14 (plate 14) and M5
(plate 25)** from the complete production project. They share one screw and both
M5 locating pins; use a 10 mm OD x 4 mm ID x 1 mm washer. Check the seated fit
before printing the other M sections. The fit coupons add material beyond the
3.330 kg production estimate.

To regenerate these two exports with OpenSCAD (from the repository root):

```powershell
$openscad = 'C:\Program Files (x86)\OpenSCAD\openscad.exe'
& $openscad --hardwarnings --camera=0,0,0,0,0,0,700 --export-format=binstl -D 'fast_preview=false' -D 'view_mode="fit_sample"' -o working/stl/Dara-Print-Checks/Photo-Fit-Sample.stl working/Dara-Photo-Frame-A1-Jointed.scad
& $openscad --hardwarnings --camera=0,0,0,0,0,0,700 --export-format=binstl -D 'fast_preview=false' -D 'view_mode="wall_fit_sample"' -D 'wall_mount_index=1' -o working/stl/Dara-Print-Checks/Wall-Fit-Sample-B1.stl working/Dara-Photo-Frame-A1-Jointed.scad
```

After regeneration, recheck connected solids (three photo / two wall), Z=0,
watertightness and hashes; the manifest describes the reviewed exports only.
