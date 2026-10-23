# Complete A1 project with flat M cores and veneers

Open [Dara-Photo-Frame-A1-Complete.3mf](Dara-Photo-Frame-A1-Complete.3mf) as a project in Bambu Studio. This alternate A1 design contains **36 saved native slices, 76 assembly pieces and one optional finish sample**. The repository-root project is the separate A2L design; their M sections and hardware are not interchangeable.

All six veneer carriers on plates 31–36 have the removable-carrier correction: separate grounded ribs, accessible 1.2 mm necks, 0.4 mm rear recesses and 3 mm rear cutting clearance. The continuous shoe and its L-shaped lip are removed. All other 30 plates retain their saved toolpaths. See the [audit of every saved veneer](../../../output/development/m-veneer-cosmetic-fit/All-veneer-production-audit.json).

The M has six flat structural cores and six matching hammered veneers with zero nominal cosmetic seam gap. All veneers share the complete saved M5 rotation: a 55-degree lean across X, with their broad face planes parallel to bed Y travel. Do not rotate veneers independently. Flat backs retain 0.20 mm glue clearance above the cores. The five cover bands are removed.

| Plates | Contents |
| --- | --- |
| 1–20 | Original knot sections F1–F20; saved slices and geometry retained |
| 21–26 | Flat structural M cores C1–C6 |
| 27–28 | Eight original backers |
| 29 | Four original wall blocks and 32 retainers |
| 30 | Original optional white, wood and blue finish sample |
| 31–36 | Veneers V1–V6 with bonded fin carriers and supplementary tree supports |

The obsolete glue-practice sample formerly on plate 32 is retained in the [archived solid-M project](../../../reference/production/Dara-Solid-M-Baseline.3mf). Use the [current zero-gap sample project](../../../output/development/m-veneer-cosmetic-fit/All-Development-Tests-A1-Sliced.3mf) for the current joint tests. Removing the old sample keeps the main project within Studio's 36-plate limit without moving the production knot or hardware plates.

Use [PRINT-READINESS.md](PRINT-READINESS.md), the [current plate guide](../../../docs/M-PRINT-GUIDE.md) and [printable map](../../../output/pdf/Dara-Part-and-Plate-Map.pdf). The current release report is [m-veneer-release-validation.json](m-veneer-release-validation.json). The mirrored-joint and cover-crown reports describe the archived solid-M release; their hashes are not the current main-project hash.

After fetching this branch and downloading Git LFS assets, audit the A2L and alternate A1 production files with standard Python:

```sh
python scripts/audit_dara_release.py
```

The projects embed geometry, support painting, filament assignments and native G-code. Scratch files and Python geometry packages are not needed to open or print them. Physical fit, silk support removal and finish confirmation remain part of the sample/full-part checks.
