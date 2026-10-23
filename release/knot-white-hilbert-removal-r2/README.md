# Original white finish restored; screw-skin correction retained

The user requested removal of the Hilbert loops while preserving the hidden
screw reinforcements. Root `Knot.3mf` is restored byte-for-byte from the validated
screw-skin release in commit `c8f8f7a`, including all ten stored native slices.
The white show face uses its original monotonic-line pattern and directions.
The Hilbert height ranges and redundant explicit blue pattern overrides are
removed. The brown texture and blue trim retain their original paths.

All 50 screw reinforcement modifiers still end at **Z12.4 mm**, beneath the
nominal Z13.5 show face and five continuous solid top layers. Their 100% infill,
the actual screw holes, other geometry, CAD/STL, print poses and all other
settings remain unchanged. The project SHA-256 is:

`8a76b70a1c1430d74a16ec06c9689827d33f3902afb1d7de90e4436072c251c3`

`validation.json` records the input/output hashes, identical mesh XML and global
process settings, narrowly scoped object/volume setting comparison, all ten
restored G-code hashes, and protected file hashes. The exact restored project
matches `../knot-reinforcement-skin-r1/validation.json`, including the verified
extrusion crossing each former cylinder boundary on all five skin layers.
Restoring the complete validated project and matching toolpaths requires no new
slice. The release catalog, native estimates and stored G-code checksums are
synchronized to this restored file. Unrelated stencil work is preserved.
The restored project reopened successfully in native Bambu Studio, and the
root release audit passed for all seven projects and 30 plates.

The Hilbert revision in `../knot-white-hilbert-r1/` is withdrawn. Current native
estimates are **80h 32m and 2271.52 g** for all ten plates. Digital verification
does not confirm physical surface finish; that remains pending. No printer job
was sent.
