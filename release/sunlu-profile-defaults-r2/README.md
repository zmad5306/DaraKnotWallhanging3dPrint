# SUNLU preset defaults — October 23, 2026

The user approved promoting the enumerated project overrides into their existing Bambu Studio presets. The three changed presets were installed in the local user filament library with their names and IDs preserved. A1 Basic is included as an unchanged reference.

| Preset | Textured PEI first / subsequent | Maximum volumetric speed |
| --- | --- | --- |
| SUNLU PLA Basic — A1 0.4 | 65 / 65 C, unchanged | 12 mm3/s, unchanged |
| SUNLU PLA Basic — A2L 0.4 | **55 / 55 → 65 / 65 C** | 12 mm3/s, unchanged |
| SUNLU PLA Metallic — A1 0.4 | 65 / 65 C, unchanged | **12 → 7.5 mm3/s** |
| SUNLU PLA Metallic — A2L 0.4 | **55 / 55 → 65 / 65 C** | **12 → 7.5 mm3/s** |

All other JSON values and profile identities are unchanged. `presets/` contains the exact current files. `validation.json` records before/after hashes, the exact field differences, native import results and installed-file readback checks. Backups and account-specific `.info` sidecars remain local under `.work/`; they are not part of the shared preset snapshots.

All four presets passed Bambu's native loader and matched 134 compared options after export to temporary projects. The CLI requires `type: filament`, which was added only to temporary import wrappers. Each profile was tested independently to avoid the CLI's observed multi-profile dryer-array interleaving; neither those temporary files nor their slices replace production files. The installed user JSON retains its original format.

The installer changed each modified preset's normal synchronization state and timestamp while preserving its existing account/profile identity, following [Bambu's preset sidecar handling](https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/Preset.cpp). Local installation is verified. Bambu account synchronization is pending the app's normal sync and has not been remotely verified.

All seven production project hashes are unchanged by this operation. Knot and Small Parts now match the new defaults in their assigned slots. Letter's unused Basic/Metallic slots retain their saved 55 C temperatures and 12 mm3/s Metallic limit. Photo Cut Aligner's unused Metallic slot retains 12 mm3/s. Those embedded values are preserved; do not reapply presets to saved projects without reviewing the changes. Letter's actual ERYONE copper remains 55 C and 7.5 mm3/s.

No reslice or printer job was sent, and no new physical qualification is claimed. `scripts/update_sunlu_preset_defaults.py` records the revision-specific preparation, native validation and installation.
