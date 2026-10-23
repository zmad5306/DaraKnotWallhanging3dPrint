# White knot Hilbert finish — withdrawn

**Withdrawn at the user's request on 2026-10-23.** Root `Knot.3mf` now restores
the original monotonic-line white finish while retaining the screw-skin correction.
This directory records the superseded Hilbert revision, not the current release.
See `../knot-white-hilbert-removal-r2/` for the restoration. Do not reapply the
historical Hilbert builder without a new request.

The user requested Hilbert curve on the white knot surfaces, explicitly
preserving the already textured brown areas, and asked whether the blue trim
would cause a problem. The revised `Knot.3mf` applies Hilbert only to the main
white show face. Each blue material modifier explicitly retains its original
monotonic-line top pattern. Brown geometry and modifier settings are unchanged.

A native height range from Z13.0 to Z13.6 selects the white show face without
changing the lower joint seating surfaces or taller locating-pin tops. Its
0.20 mm layer-height and extruder 0 (inherit) entries match Bambu's native range
defaults. The global top pattern stays monotonic-line. Top line width stays
0.42 mm; no speed, material, temperature, flow or infill tuning is included.
The five solid top layers and all 50 Z12.4 screw reinforcement modifiers remain.

All ten plates have fresh native slices. Verification compares the complete
brown and blue model-extrusion centerlines, all white model paths below the show
face and above it, and the white show-face walls against the input release.
Centerlines are compared at the G-code's 0.001 mm precision, independent of
travel order and segment reversal. White top paths must show the two perpendicular
Hilbert directions, and no white centerline may enter the blue material region.
Mesh XML and saved poses are preserved exactly. The native round-trip, process
constants, layer/filament heights, G-code hashes, bed/tower clearances and final
native reopen are checked separately. CAD and all STL files remain byte-identical.

- `provenance.json`: source hash, exact setting changes and protected files.
- `validation.json`: current hash, preservation signatures, boundary checks,
  native reopen and time/material estimates.
- `native-result.json`: native slicer result.
- `white-blue-before-after.png`: actual plate-3 top-layer paths at Z13.6.

The previous screw-skin evidence remains at `../knot-reinforcement-skin-r1/`.
It describes the restored current release; this directory identifies the superseded Hilbert slices.
No printer job was sent. A physical print is still needed to judge appearance,
sheen and feel; a Hilbert path is not proof of a fabric-like result.

Native estimate for all ten plates: **86h 59m, 2270.31 g**. Compared with the
preceding screw-skin release, this adds about **6h 27m (8%)**; material use drops
by about 1.20 g. These are slicer estimates, not measured print results.

Reproduction: `scripts/apply_knot_white_hilbert.py`, using sequential `build`,
`slice`, `validate` and `publish` actions against the recorded source hash.
Native schema references: [Bambu's range exporter](https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/Format/bbs_3mf.cpp)
and [range defaults](https://github.com/bambulab/BambuStudio/blob/master/src/slic3r/GUI/GUI_ObjectList.cpp).
