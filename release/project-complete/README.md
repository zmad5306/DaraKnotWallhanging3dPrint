# Project complete — November 2, 2026

The owner confirms: “Printing and assembly are complete. Its ready for xmas morning.” The completed wall hanging is ready for Christmas morning. Earlier physical-status notes document what was known at each revision; they are retained as history.

The seven root production projects, their adjacent CAD/STL, saved settings and slices are preserved without modification. The latest Letter rear-brace correction and right-hand wall-block correction remain the production baseline.

## Source capture

`source-manifest.json` records 420 historical source files from the repository's ignored development folders and the original Nextcloud v26 source/CAD folders. Byte-identical sources already captured in Git are referenced rather than copied. Other sources are preserved under `archive/development-sources/`, including the original source folder's mesh dependencies. Paths and SHA-256 hashes preserve provenance.

These are historical working sources, not alternative production releases. Some scripts depend on retired local artifacts or machine-specific paths. Do not run them over the completed production files. The seven root projects and the existing approved ERYONE sample remain the tracked print-project inventory. Retired 3MF files, generated scratch meshes, installed libraries, caches, unrelated printer accessories and the separate SUNLU inventory-repair work remain local.

The previously uncaptured veneer candidate documentation and inspection records are retained under their existing `output/` folders. The clamp-protector generator and its source/documentation are also captured; its separate print project remains local under the existing print-project policy.

## Verification

`integrity.json` records current catalog hash checks for all seven production projects, all seven CAD entry files and every catalogued STL occurrence. The source manifest hashes were checked against their captured files. No geometry regeneration, reslicing or printer operation was performed.

The older `audit_root_projects.py` passes Knot but stops at its outdated Letter hash expectation, which predates the committed rear-brace correction. This is recorded rather than rewriting historical validation evidence or claiming a complete audit pass. Current artifact integrity was checked directly against the current release catalog.
