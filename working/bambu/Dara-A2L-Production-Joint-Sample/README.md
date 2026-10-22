> **Historical record:** the 3MF files in this folder are retired from source control. Use the root project guide at the repository root. This document records the original revision; retrieve commit `5dab12a` and its LFS objects if the historical projects are needed.

# Production joint sample — A2L

Open **[Dara-A2L-Production-Joint-Sample.3mf](Dara-A2L-Production-Joint-Sample.3mf)** as a project and print plate 1. It contains the **J4 joint: F4 tongue and F3 socket**, cropped directly from the saved root `Dara.3mf`.

Estimated print: **1 h 36 min / 36.8 g**, including support and purge. Saved setup: A2L, 0.4 mm nozzle, 0.20 mm layers, Textured PEI; white/wood/blue slots 1/2/4.

The production keys, pads, tongue/mortise fit, decorative surfaces and material modifiers are retained within the sample crop. Each piece also retains its production print rotation, infill direction and object settings. The objects and purge tower are placed on one sample plate. No clearance relief or simplified-joint changes have been applied.

**Corrected crop:** the sample is cut at the 67.3035 mm straight ribbon span. The old 69.3035 mm crop included 1 mm of the adjacent rounded openings on each side, producing the two visible scallops. Cropping at the ribbon span gives straight sample boundaries without adding or reshaping production material. See the [full-production comparison and 14-joint audit](../../review/production-side-notches/README.md).

This tests the current production joint. Remove its supports and brim, dry-fit the two pieces, and check seating, surface alignment and appearance. Production fit has not been qualified by these digital checks.

Source SHA-256: `b943790d7deefbaa22413106848dd936ccbe26b294372be4d85ea5dee578425d`.

Validation covers exact crop preservation, straight sample side boundaries, retained material volumes and settings, preserved source rotations, closed connected parts, original Z5.0 pad contacts, native mesh/pose agreement, actual white/wood/blue finish heights, six pad toolpath probes, supports, bed bounds, purge-tower clearance and G-code checksum. See [geometry checks](geometry-validation.json) and [native slice checks](native-validation.json). Production files and every A1 companion file remain unchanged. No printer job was sent.

The [editable source](Dara-A2L-Production-Joint-Sample-Editable.3mf) is also included. Reproduce with `scripts/extract_production_joint_sample.py build`, then `slice`, then `validate`, using the existing repository dependencies and installed Bambu Studio.
