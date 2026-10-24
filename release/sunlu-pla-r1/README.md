# SUNLU PLA profile assignments — October 23, 2026

This folder records the project identity migration and the presets at that time. The subsequently approved current defaults are in [sunlu-profile-defaults-r2](../sunlu-profile-defaults-r2/README.md); its preset snapshots supersede the older snapshots here. The project hashes and preservation evidence in this folder remain current because the later operation changes local presets only.

The user created SUNLU PLA Basic and SUNLU PLA Metallic presets for A1 and A2L and requested replacing Generic PLA assignments after checking the settings. The comparison found the exceptions below; the user explicitly chose to apply the SUNLU identities while retaining the saved project overrides.

| Project | SUNLU PLA Basic slots | SUNLU PLA Metallic slots | Retained project overrides |
| --- | --- | --- | --- |
| Knot | 1 white, 2 wood tan | 4 Azurite blue | Slots 1/2/4: Textured PEI bed 65 C first/subsequent, versus 55 C preset; slot 4: 7.5 mm3/s flow limit, versus 12 |
| Letter | 1 white, 2 wood tan | 4 Azurite blue | None |
| Small Parts | 1 white, 2 wood tan | 4 Azurite blue | Slot 4: 7.5 mm3/s flow limit, versus 12 |
| Small Parts - Photo Cut Aligner | 2 wood tan | 4 Azurite blue | None; active transparent PLA slot 1 preserved |
| Small Parts - Sanding Block PLA | 1 | None | None; saved blue display color preserved |
| Small Parts - Crate Stencils | 1 white | None | None |

Each project uses the preset for its actual saved printer and 0.4 mm nozzle. SUNLU Basic and Metallic have identical printing settings within each printer, with separate names and filament IDs. Their common settings are 220 C nozzle first/subsequent, 0.98 flow ratio, 60–80% fan, 20 mm/s minimum cooling speed and 12 mm3/s maximum volumetric speed before the retained blue overrides. Textured PEI defaults are 65 C on A1 and 55 C on A2L. These were compared with the actual project settings, which were saved as Generic PLA; the printer's default Bambu PLA Basic label is not the project's assigned filament.

`presets/` contains exact snapshots of the four local user presets. `validation.json` records their source paths and hashes, every compared option, all preserved exceptions, before/after project hashes, per-plate G-code hashes and native reopen results. Dryer arrays were compared as complete per-material tuples and retained in their original serialization. Existing colors and assignments remain unchanged. Each replaced slot was checked against 134 preset options. All six projects also passed native load/save verification with every one of their 583 or 584 project settings unchanged; the full seven-project repository audit passed.

Only `filament_settings_id`, `filament_vendor` and `filament_ids` change in the saved project settings. Corresponding G-code configuration comments and MD5 checksums are updated, together with the slice metadata's material IDs. All other G-code bytes are identical across 29 plates, so no reslice is required and existing time/material estimates remain applicable. All meshes, support paint, transforms, object/volume settings, process values, temperatures, speeds, cooling, purge settings and protected CAD/STL files are preserved. Existing solid regions and stencil process exceptions remain intact.

Copper silk, Letter's approved ERYONE profile, transparent PLA and PETG are not reassigned. The successful ERYONE sample is preserved at its recorded physical-evidence hash. Historical/local sample projects are not updated. No printer job was sent and physical qualification has not changed.

Run `python scripts/audit_root_projects.py` to verify the current releases. The audit links the new identity metadata to the previous geometry/toolpath reports and validates current checksums. `scripts/apply_sunlu_pla_profiles.py` records the revision-specific migration and requires the original source hashes; it is not a general regeneration command.
