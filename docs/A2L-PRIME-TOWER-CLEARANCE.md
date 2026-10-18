# A2L prime-tower clearance correction

The first A2L release completed native slicing without a toolpath conflict but displayed **“Prime Tower is too close to others”** in Studio's Prepare view. That release check was incomplete: it allowed towers in concave artwork openings.

Studio's `layered_print_cleareance_valid` checks the tower against the convex XY projection of each actual model volume. A concave opening can lie inside that projection. The source is [Bambu Studio Print.cpp](https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/Print.cpp). The warning was reproduced by opening the distributed `Dara.3mf` in the local Studio GUI.

The correction moves towers on all ten multicolor knot plates into bed corners outside the actual model convex hull. The planner reserves a 38 × 38 mm rectangle for each current ribbed tower and its 2 mm brim and requires more than 8 mm additional distance to the model hull. It maximizes that distance over legal bed positions. No part mesh, part rotation, joint, filament or infill change is needed.

The final native gate uses the **emitted tower extrusion**, rather than only an assumed rectangle. It checks that the complete bead envelope fits inside the reserved rectangle, remains outside all model hulls, stays on the A2L bed and is more than 3 mm from all other extrusion, including supports and brims. Future changes to purge/tower settings that enlarge its real footprint must pass this gate again. `tower-placement.json` and each knot plate's `prime_tower_clearance` entry in `native-validation.json` record the results. The portable release audit checks these results and their evidence hashes.

The second notice, about **thermal preconditioning**, explains warm-up timing and the white bed-zone guides. It is informational. This correction does not disable preconditioning, change its preference or hide warnings.

Use the refreshed complete project, not the previously opened in-memory copy. Open `Dara.3mf` **as a project** after pulling the branch and Git LFS files. Retain its saved model and tower positions; don't auto-arrange them independently.

The corrected native checks pass on all ten multicolor plates, with a minimum **41.9 mm** bead-to-bead distance to other printed material. Native slicing and reopen both pass. The local Studio GUI stopped responding while opening the corrected editable project, so visual confirmation that its banner cleared is pending; this is recorded explicitly in `tower-gui-verification.json`. No printer commands were sent.
