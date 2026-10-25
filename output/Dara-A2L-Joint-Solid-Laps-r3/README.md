# Solid overlapping laps — r3 experiment

## User-reported result — October 25, 2026

The user reported **"Solids work wonderfully"** and requested propagation, commit and push. This is user-reported success for the supplied r3 sample, SHA-256 `6898ed006c82b81beafe6a90012c3e59d23e4124a75daf22d50db93e8a2a447c`; the actual printed hash/printer were not independently observed. Its solid-lap settings are now promoted to the main `Knot.3mf`; see `release/knot-solid-laps-r1/`. Full-size performance and bolster appearance are not independently established by this statement. The preparation notes below describe the sample's creation before promotion; their digital checks remain historical evidence.

Use **Dara-A2L-Joint-Solid-Laps-r3.3mf**. Open as a **project** in Bambu Studio. One A2L plate with the same two J3 F2/F3 pieces and photo-retainer blind-hole bolster as the accepted r2 sample.

Estimate: **2h 11m / 54.74 g**, including supports and tower.

The only printing change is **100% rectilinear fill in BOTH overlapping lap sections**, joint-local X0–18 mm across the full crop width. These local settings modifiers cover Z0–13.5 and affect only existing model stock: the lower tongue, its keys, and the matching upper socket section. They add no material to the glue gap, key grooves, screw hole or photo openings. Full-thickness bodies outside the overlap remain **8% gyroid**. Rectilinear is used only in the laps because native inspection of 100% gyroid still showed open channels. This is a requested clamping experiment; resistance to deformation has not yet been physically established.

Unchanged: all eight original model/color/bolster volumes, joint clearances, crop X−14–66 / Y−38–38 mm, rotations and bed positions, materials, finish directions, normal supports, infill-first OFF, 0.4 mm nozzle, 0.20 mm layers, four walls, five top/bottom layers and Textured PEI. No new crop or translation was made. The accepted sample's recorded production source is `Knot.3mf` SHA-256 `aefab9b242945a149fdc18900c694c556eb7ad5d8d5d5f7fbc4451280730ae46`.

The actual **photo-retainer bolster** is still 14 mm diameter / 100% infill, ending at **Z12.4** below the exposed Z13.5 face and its five top layers. Its 3.175 mm blind bore ends at Z10.7. This feature lies outside the solid-lap region. The native slice was checked for the capped bolster and covered face.

Remove normal supports from both grooves before dry fitting. Support also remains inside the photo-retainer blind bore; remove it from the back if checking the screw. Check joint fit and face alignment, then clamping behavior. The r2 joint-fit report does not physically qualify this new infill revision.

Validation checks all original geometry/settings against r2, dense native extrusion on every lap layer, retained sparse body infill, key clearances, material boundaries, groove backing, photo-retainer skin, bed/tower clearance, G-code checksum and native reopen. First layers over supports can use the preserved bridge spacing; a 100% modifier does not change bridge settings or promise a void-free physical print.

Production and accepted r2 remain unchanged. No print job was sent. r2 remains the accepted reference; r1 remains withdrawn for the wrong screw feature. This r3 is the current **solid-lap experiment**, not a production promotion.

- Accepted r2 SHA-256: `c0e48a0b2f7c8bf8adcc696b9785d4ff49359dd9104536ca486a1ec50055154d`
- This r3 SHA-256: `6898ed006c82b81beafe6a90012c3e59d23e4124a75daf22d50db93e8a2a447c`
- Evidence: `geometry-validation.json`, `photo-retainer-audit.json`, `validation.json` and `native-result.json`.
