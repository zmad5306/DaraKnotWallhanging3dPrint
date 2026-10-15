# Complete A1 print project

Open [Dara-Photo-Frame-A1-Complete.3mf](Dara-Photo-Frame-A1-Complete.3mf) as a project in Bambu Studio. It is byte-identical to [Dara.3mf](../../../Dara.3mf) at the repository root. Both contain 32 saved native slices, 75 assembly pieces and three optional sample pieces.

Use [PRINT-READINESS.md](PRINT-READINESS.md) for the current plate map, filament slots, settings, band locations and assembly order. The embedded meshes and process settings are the production source. The M is full size, hammered and oriented at 55 degrees with its face plane along Y. The five copper covers now use continuous circular-section crowns. Their native paths remove the repeated middle-face junction tracks while preserving the seating surfaces within 0.0002 mm. Three isolated end transitions remain, as shown in the [path comparison](../../review/continuous-covers/before-after-paths.png). Resolution is now 0.05 mm globally; the other 31 saved slices are unchanged. Physical printing of this revision remains pending.

[cover-crown-validation.json](cover-crown-validation.json) is the current release report. Older reports in this folder describe earlier stages and are not the current release checksum. The old flat M STL exports and PDF map do not describe the new M cuts or covers. Do not run historical flat-M project publishers against this file.

After `git lfs pull`, audit both copies without any experimental dependencies:

```powershell
python scripts/audit_dara_release.py
```

The parametric generator and migration history remain on [codex/hammered-m-production](https://github.com/zmad5306/DaraKnotWallhanging3dPrint/tree/codex/hammered-m-production). The 3MF embeds all meshes, support painting, filament assignments and toolpaths needed for Studio; no standalone candidate or test project is required.
