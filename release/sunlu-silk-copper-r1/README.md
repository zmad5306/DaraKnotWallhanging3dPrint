# SUNLU PLA Silk Copper — October 23, 2026

The user requested a custom Bambu filament matching the copper SUNLU silk settings already saved in the projects. The installed custom filament has two presets:

- **SUNLU PLA Silk Copper @Bambu Lab A1 0.4 nozzle**, copied from Small Parts slot 3.
- **SUNLU PLA Silk Copper @Bambu Lab A2L 0.4 nozzle**, copied from Knot slot 3.

| Setting | Both presets |
| --- | --- |
| Nozzle, first / subsequent | 220 / 220 C |
| Textured PEI bed, first / subsequent | 55 / 55 C |
| Flow ratio | 0.98 |
| Maximum volumetric speed | 7.5 mm3/s |
| Fan minimum / maximum | 60 / 80% |
| Minimum cooling slowdown speed | 20 mm/s |
| Filament retraction length | 0.5 mm |
| Default copper color | #B87333 |

Every one of the 134 compared filament options matches its source slot, including plate temperatures, cooling, retraction, purge parameters, dryer tuples and each printer's exact saved filament start/end G-code. These are full independent user base presets with SUNLU vendor identity and one shared custom filament ID; the material type remains PLA. The custom ID follows [Bambu Studio's custom-filament naming and ID convention](https://github.com/bambulab/BambuStudio/blob/master/src/slic3r/GUI/CreatePresetsDialog.cpp).

`presets/` contains exact installed JSON snapshots. `validation.json` records source project hashes, option comparisons, native Bambu load/export results and installed-file readback. All 134 options also matched after independent native loading. Account-specific sidecars are local only and mark the new presets for normal account sync; remote sync has not been verified.

This creates the presets only. It does not change any project assignment, mesh, process setting or stored slice, and it does not replace Letter's approved ERYONE copper. All seven project hashes and all pre-existing local presets were checked unchanged during creation. No physical calibration or printer job was performed.

`scripts/create_sunlu_copper_preset.py` records the guarded creation and installation. The current Basic and Metallic presets are documented separately in [sunlu-profile-defaults-r2](../sunlu-profile-defaults-r2/README.md).
