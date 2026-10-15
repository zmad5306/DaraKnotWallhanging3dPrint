# Complete A1 print project

Open [Dara-Photo-Frame-A1-Complete.3mf](Dara-Photo-Frame-A1-Complete.3mf) as a project in Bambu Studio. It is byte-identical to [Dara.3mf](../../../Dara.3mf) at the repository root. Both contain 32 saved native slices, 75 assembly pieces and three optional sample pieces.

Use [PRINT-READINESS.md](PRINT-READINESS.md) for the current plate map, filament slots, settings, band locations and assembly order. The frame has 20 sections and 32 mirrored seams, each 67.3-75.1 mm long, using the same 18 mm keyed-lap profile. The revised rear attachments match the hammered M. Plates 1-20, 21, 23 and 26 are regenerated; the other nine saved slices and their meshes are unchanged. The M keeps its hammered face and 55-degree orientation along Y. The five continuous copper crowns and their plate 31 slice are preserved. Resolution remains 0.05 mm globally. Physical printing of this revision remains pending.

[mirrored-joints-validation.json](mirrored-joints-validation.json) is the current release report. [cover-crown-validation.json](cover-crown-validation.json) records the preceding cover revision, which is retained here. Older reports are historical rather than current release checksums. The [updated PDF map](../../../output/pdf/Dara-Part-and-Plate-Map.pdf) covers the current frame and hammered M. The flat M STL exports remain historical. Do not run historical flat-M project publishers against this file.

After `git lfs pull`, audit both copies without any experimental dependencies:

```powershell
python scripts/audit_dara_release.py
```

The parametric generator and migration history remain on [codex/hammered-m-production](https://github.com/zmad5306/DaraKnotWallhanging3dPrint/tree/codex/hammered-m-production). The 3MF embeds all meshes, support painting, filament assignments and toolpaths needed for Studio; no standalone candidate or test project is required.
