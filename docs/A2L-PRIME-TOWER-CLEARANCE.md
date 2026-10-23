# A2L prime-tower clearance correction

Studio 02.08.02.61 **overrides the saved A2L tower Y position with 160 mm** when opening a project. It also clamps tower X to the machine's margins. The previous corner positions were valid in the native CLI slice but were moved into the knot when the GUI loaded them. A GUI-saved diagnostic project confirmed this: every tower Y changed to 160. `tower-GUI-position-reset.json` records the input and GUI-effective values.

The installed source identifies the cause in `PartPlateList::set_default_wipe_tower_pos_for_plate`: for printer type N9 (A2L), it unconditionally assigns `N9_WIPE_TOWER_DEFAULT_Y_POS`. Changing only the saved corner coordinates cannot fix that load behavior.

## Current layout

All towers now use **Y160**, with legal X positions chosen from the actual knot projection. Studio therefore keeps these positions on load. Prime and purge volumes are unchanged. Conventional rectangular towers avoid unnecessary ribbed placeholders on single-color plates; smooth timelapse stays off.

Studio also checks the convex hull of each model volume, which fills in concave artwork openings. To permit a tower in a genuinely empty opening, each knot's model is represented by adjoining volumes around its reserved tower envelope, all in **one object with the same material**. Their exact boolean union equals the original printable solid. These are slicer volumes, **not additional pieces or assembly joints**: the knot still has ten pieces and 14 joints. Colors, reinforcement, object settings, all 61 saved part poses, and the complete M geometry remain unchanged. All 51 M/accessory model assets are byte-identical.

The planner reserves a 36 x 40 mm envelope including brim, requires more than 8 mm model-volume hull clearance and preserves the original part positions. The native gate checks the actual emitted tower, supports, brims, bed bounds, and all 20 startup estimates. The tower locations also pass the installed GUI's Y160/X-margin reset rules.

The build requires negligible added/removed boolean volume. A comparison against the previous distributed release checks model extrusion and outer-wall extrusion on all ten knot plates; this would catch the addition of substantial internal partition walls. Results and G-code hashes are in `knot-volume-toolpath-comparison.json`. Normal geometry, zero-gap cosmetic edges, modifier round trips, material directions and fin bonds are checked independently.

The byte-identical final native project was opened through Studio's Open Project dialog with the A2L profile retained. **The prime-tower collision banner is absent.** `tower-gui-verification.json` records that GUI pass and the tested SHA. The **thermal preconditioning** notice remains visible because it is informational. Across all ten knot plates, outer-wall extrusion changes by less than 0.006% and total model extrusion by less than 0.166% relative to the previous distributed release.

Open the refreshed `Dara.3mf` **as a project** from disk after pulling the branch and Git LFS files. An already-open project retains its old settings. Keep saved part rotations and tower positions.

Official installed-version source:

- [PartPlate.cpp](https://github.com/bambulab/BambuStudio/blob/v02.08.02.61/src/slic3r/GUI/PartPlate.cpp): `PartPlateList::set_default_wipe_tower_pos_for_plate` and N9 Y160.
- [Print.cpp](https://github.com/bambulab/BambuStudio/blob/v02.08.02.61/src/libslic3r/Print.cpp): `layered_print_cleareance_valid`, `has_wipe_tower`, `wipe_tower_data`.
- [WipeTower.cpp](https://github.com/bambulab/BambuStudio/blob/v02.08.02.61/src/libslic3r/GCode/WipeTower.cpp): tower height/depth limits.

No printer commands were sent. Physical joint, silk-finish and load tests remain pending.
