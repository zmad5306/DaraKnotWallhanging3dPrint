// Exact mesh-based CAD snapshot of Knot.3mf.
// Uses the supplied STL volumes; this is not a parametric feature history.
// Dimensions, material regions, print poses and modifiers come from the saved project.
plate = 1; // Select the plate to inspect. 0 shows all plates.
show_modifiers = false;

// Plate 1: F1 A2L knot; volume 1; normal_part
if ((plate == 0 || plate == 1))
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.194963642, -0.98081047, 0.0, 149.219068], [0.98081047, -0.194963642, 0.0, 298.872868], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F1-A2L-knot-volume-1.stl", convexity=20);

// Plate 1: F1 A2L knot; volume 2; normal_part
if ((plate == 0 || plate == 1))
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.194963642, -0.98081047, 0.0, 149.219068], [0.98081047, -0.194963642, 0.0, 298.872868], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F1-A2L-knot-volume-2.stl", convexity=20);

// Plate 1: F1 A2L knot; volume 3; normal_part
if ((plate == 0 || plate == 1))
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.194963642, -0.98081047, 0.0, 149.219068], [0.98081047, -0.194963642, 0.0, 298.872868], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F1-A2L-knot-volume-3.stl", convexity=20);

// Plate 1: F1 A2L knot; volume 4; modifier_part
if ((plate == 0 || plate == 1) && show_modifiers)
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.194963642, -0.98081047, 0.0, 149.219068], [0.98081047, -0.194963642, 0.0, 298.872868], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F1-A2L-knot-volume-4.stl", convexity=20);

// Plate 1: F1 A2L knot; volume 5; modifier_part
if ((plate == 0 || plate == 1) && show_modifiers)
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.194963642, -0.98081047, 0.0, 149.219068], [0.98081047, -0.194963642, 0.0, 298.872868], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F1-A2L-knot-volume-5.stl", convexity=20);

// Plate 1: F1 A2L knot; volume 6; modifier_part
if ((plate == 0 || plate == 1) && show_modifiers)
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.194963642, -0.98081047, 0.0, 149.219068], [0.98081047, -0.194963642, 0.0, 298.872868], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F1-A2L-knot-volume-6.stl", convexity=20);

// Plate 1: F1 A2L knot; volume 7; modifier_part
if ((plate == 0 || plate == 1) && show_modifiers)
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.194963642, -0.98081047, 0.0, 149.219068], [0.98081047, -0.194963642, 0.0, 298.872868], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F1-A2L-knot-volume-7.stl", convexity=20);

// Plate 1: F1 A2L knot; volume 8; modifier_part
if ((plate == 0 || plate == 1) && show_modifiers)
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.194963642, -0.98081047, 0.0, 149.219068], [0.98081047, -0.194963642, 0.0, 298.872868], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F1-A2L-knot-volume-8.stl", convexity=20);

// Plate 1: F1 A2L knot; volume 9; modifier_part
if ((plate == 0 || plate == 1) && show_modifiers)
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.194963642, -0.98081047, 0.0, 149.219068], [0.98081047, -0.194963642, 0.0, 298.872868], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F1-A2L-knot-volume-9.stl", convexity=20);

// Plate 2: F2 A2L knot; volume 1; normal_part
if ((plate == 0 || plate == 2))
 translate(plate == 0 ? [396.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.0396014862, -0.999215553, 0.0, 308.380862], [0.999215553, -0.0396014862, 0.0, 483.341335], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F2-A2L-knot-volume-1.stl", convexity=20);

// Plate 2: F2 A2L knot; volume 2; normal_part
if ((plate == 0 || plate == 2))
 translate(plate == 0 ? [396.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.0396014862, -0.999215553, 0.0, 308.380862], [0.999215553, -0.0396014862, 0.0, 483.341335], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F2-A2L-knot-volume-2.stl", convexity=20);

// Plate 2: F2 A2L knot; volume 3; normal_part
if ((plate == 0 || plate == 2))
 translate(plate == 0 ? [396.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.0396014862, -0.999215553, 0.0, 308.380862], [0.999215553, -0.0396014862, 0.0, 483.341335], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F2-A2L-knot-volume-3.stl", convexity=20);

// Plate 2: F2 A2L knot; volume 4; normal_part
if ((plate == 0 || plate == 2))
 translate(plate == 0 ? [396.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.0396014862, -0.999215553, 0.0, 308.380862], [0.999215553, -0.0396014862, 0.0, 483.341335], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F2-A2L-knot-volume-4.stl", convexity=20);

// Plate 2: F2 A2L knot; volume 5; modifier_part
if ((plate == 0 || plate == 2) && show_modifiers)
 translate(plate == 0 ? [396.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.0396014862, -0.999215553, 0.0, 308.380862], [0.999215553, -0.0396014862, 0.0, 483.341335], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F2-A2L-knot-volume-5.stl", convexity=20);

// Plate 2: F2 A2L knot; volume 6; modifier_part
if ((plate == 0 || plate == 2) && show_modifiers)
 translate(plate == 0 ? [396.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.0396014862, -0.999215553, 0.0, 308.380862], [0.999215553, -0.0396014862, 0.0, 483.341335], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F2-A2L-knot-volume-6.stl", convexity=20);

// Plate 2: F2 A2L knot; volume 7; modifier_part
if ((plate == 0 || plate == 2) && show_modifiers)
 translate(plate == 0 ? [396.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.0396014862, -0.999215553, 0.0, 308.380862], [0.999215553, -0.0396014862, 0.0, 483.341335], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F2-A2L-knot-volume-7.stl", convexity=20);

// Plate 2: F2 A2L knot; volume 8; modifier_part
if ((plate == 0 || plate == 2) && show_modifiers)
 translate(plate == 0 ? [396.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.0396014862, -0.999215553, 0.0, 308.380862], [0.999215553, -0.0396014862, 0.0, 483.341335], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F2-A2L-knot-volume-8.stl", convexity=20);

// Plate 2: F2 A2L knot; volume 9; modifier_part
if ((plate == 0 || plate == 2) && show_modifiers)
 translate(plate == 0 ? [396.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.0396014862, -0.999215553, 0.0, 308.380862], [0.999215553, -0.0396014862, 0.0, 483.341335], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F2-A2L-knot-volume-9.stl", convexity=20);

// Plate 2: F2 A2L knot; volume 10; modifier_part
if ((plate == 0 || plate == 2) && show_modifiers)
 translate(plate == 0 ? [396.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.0396014862, -0.999215553, 0.0, 308.380862], [0.999215553, -0.0396014862, 0.0, 483.341335], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F2-A2L-knot-volume-10.stl", convexity=20);

// Plate 2: F2 A2L knot; volume 11; modifier_part
if ((plate == 0 || plate == 2) && show_modifiers)
 translate(plate == 0 ? [396.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.0396014862, -0.999215553, 0.0, 308.380862], [0.999215553, -0.0396014862, 0.0, 483.341335], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F2-A2L-knot-volume-11.stl", convexity=20);

// Plate 3: F3 A2L knot; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [792.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.913137115, -0.40765256, 0.0, 386.9713300000001], [0.40765256, 0.913137115, 0.0, -84.441661], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F3-A2L-knot-volume-1.stl", convexity=20);

// Plate 3: F3 A2L knot; volume 2; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [792.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.913137115, -0.40765256, 0.0, 386.9713300000001], [0.40765256, 0.913137115, 0.0, -84.441661], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F3-A2L-knot-volume-2.stl", convexity=20);

// Plate 3: F3 A2L knot; volume 3; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [792.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.913137115, -0.40765256, 0.0, 386.9713300000001], [0.40765256, 0.913137115, 0.0, -84.441661], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F3-A2L-knot-volume-3.stl", convexity=20);

// Plate 3: F3 A2L knot; volume 4; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [792.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.913137115, -0.40765256, 0.0, 386.9713300000001], [0.40765256, 0.913137115, 0.0, -84.441661], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F3-A2L-knot-volume-4.stl", convexity=20);

// Plate 3: F3 A2L knot; volume 5; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [792.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.913137115, -0.40765256, 0.0, 386.9713300000001], [0.40765256, 0.913137115, 0.0, -84.441661], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F3-A2L-knot-volume-5.stl", convexity=20);

// Plate 3: F3 A2L knot; volume 6; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [792.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.913137115, -0.40765256, 0.0, 386.9713300000001], [0.40765256, 0.913137115, 0.0, -84.441661], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F3-A2L-knot-volume-6.stl", convexity=20);

// Plate 3: F3 A2L knot; volume 7; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [792.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.913137115, -0.40765256, 0.0, 386.9713300000001], [0.40765256, 0.913137115, 0.0, -84.441661], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F3-A2L-knot-volume-7.stl", convexity=20);

// Plate 3: F3 A2L knot; volume 8; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [792.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.913137115, -0.40765256, 0.0, 386.9713300000001], [0.40765256, 0.913137115, 0.0, -84.441661], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F3-A2L-knot-volume-8.stl", convexity=20);

// Plate 3: F3 A2L knot; volume 9; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [792.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.913137115, -0.40765256, 0.0, 386.9713300000001], [0.40765256, 0.913137115, 0.0, -84.441661], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F3-A2L-knot-volume-9.stl", convexity=20);

// Plate 3: F3 A2L knot; volume 10; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [792.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.913137115, -0.40765256, 0.0, 386.9713300000001], [0.40765256, 0.913137115, 0.0, -84.441661], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F3-A2L-knot-volume-10.stl", convexity=20);

// Plate 3: F3 A2L knot; volume 11; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [792.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.913137115, -0.40765256, 0.0, 386.9713300000001], [0.40765256, 0.913137115, 0.0, -84.441661], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F3-A2L-knot-volume-11.stl", convexity=20);

// Plate 3: F3 A2L knot; volume 12; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [792.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.913137115, -0.40765256, 0.0, 386.9713300000001], [0.40765256, 0.913137115, 0.0, -84.441661], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F3-A2L-knot-volume-12.stl", convexity=20);

// Plate 4: F4 A2L knot; volume 1; normal_part
if ((plate == 0 || plate == 4))
 translate(plate == 0 ? [1188.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.915804697, -0.4016239, 0.0, 384.50685999999996], [0.4016239, -0.915804697, 0.0, 405.079072], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F4-A2L-knot-volume-1.stl", convexity=20);

// Plate 4: F4 A2L knot; volume 2; normal_part
if ((plate == 0 || plate == 4))
 translate(plate == 0 ? [1188.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.915804697, -0.4016239, 0.0, 384.50685999999996], [0.4016239, -0.915804697, 0.0, 405.079072], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F4-A2L-knot-volume-2.stl", convexity=20);

// Plate 4: F4 A2L knot; volume 3; normal_part
if ((plate == 0 || plate == 4))
 translate(plate == 0 ? [1188.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.915804697, -0.4016239, 0.0, 384.50685999999996], [0.4016239, -0.915804697, 0.0, 405.079072], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F4-A2L-knot-volume-3.stl", convexity=20);

// Plate 4: F4 A2L knot; volume 4; normal_part
if ((plate == 0 || plate == 4))
 translate(plate == 0 ? [1188.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.915804697, -0.4016239, 0.0, 384.50685999999996], [0.4016239, -0.915804697, 0.0, 405.079072], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F4-A2L-knot-volume-4.stl", convexity=20);

// Plate 4: F4 A2L knot; volume 5; modifier_part
if ((plate == 0 || plate == 4) && show_modifiers)
 translate(plate == 0 ? [1188.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.915804697, -0.4016239, 0.0, 384.50685999999996], [0.4016239, -0.915804697, 0.0, 405.079072], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F4-A2L-knot-volume-5.stl", convexity=20);

// Plate 4: F4 A2L knot; volume 6; modifier_part
if ((plate == 0 || plate == 4) && show_modifiers)
 translate(plate == 0 ? [1188.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.915804697, -0.4016239, 0.0, 384.50685999999996], [0.4016239, -0.915804697, 0.0, 405.079072], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F4-A2L-knot-volume-6.stl", convexity=20);

// Plate 4: F4 A2L knot; volume 7; modifier_part
if ((plate == 0 || plate == 4) && show_modifiers)
 translate(plate == 0 ? [1188.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.915804697, -0.4016239, 0.0, 384.50685999999996], [0.4016239, -0.915804697, 0.0, 405.079072], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F4-A2L-knot-volume-7.stl", convexity=20);

// Plate 4: F4 A2L knot; volume 8; modifier_part
if ((plate == 0 || plate == 4) && show_modifiers)
 translate(plate == 0 ? [1188.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.915804697, -0.4016239, 0.0, 384.50685999999996], [0.4016239, -0.915804697, 0.0, 405.079072], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F4-A2L-knot-volume-8.stl", convexity=20);

// Plate 4: F4 A2L knot; volume 9; modifier_part
if ((plate == 0 || plate == 4) && show_modifiers)
 translate(plate == 0 ? [1188.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.915804697, -0.4016239, 0.0, 384.50685999999996], [0.4016239, -0.915804697, 0.0, 405.079072], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F4-A2L-knot-volume-9.stl", convexity=20);

// Plate 4: F4 A2L knot; volume 10; modifier_part
if ((plate == 0 || plate == 4) && show_modifiers)
 translate(plate == 0 ? [1188.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.915804697, -0.4016239, 0.0, 384.50685999999996], [0.4016239, -0.915804697, 0.0, 405.079072], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F4-A2L-knot-volume-10.stl", convexity=20);

// Plate 4: F4 A2L knot; volume 11; modifier_part
if ((plate == 0 || plate == 4) && show_modifiers)
 translate(plate == 0 ? [1188.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.915804697, -0.4016239, 0.0, 384.50685999999996], [0.4016239, -0.915804697, 0.0, 405.079072], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F4-A2L-knot-volume-11.stl", convexity=20);

// Plate 4: F4 A2L knot; volume 12; modifier_part
if ((plate == 0 || plate == 4) && show_modifiers)
 translate(plate == 0 ? [1188.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.915804697, -0.4016239, 0.0, 384.50685999999996], [0.4016239, -0.915804697, 0.0, 405.079072], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F4-A2L-knot-volume-12.stl", convexity=20);

// Plate 5: F5 A2L knot; volume 1; normal_part
if ((plate == 0 || plate == 5))
 translate(plate == 0 ? [0.0, -384.0, 0] : [0,0,0])
  multmatrix([[0.0394260095, -0.999222493, 0.0, 308.44139], [0.999222493, 0.0394260095, 0.0, -163.33550400000001], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F5-A2L-knot-volume-1.stl", convexity=20);

// Plate 5: F5 A2L knot; volume 2; normal_part
if ((plate == 0 || plate == 5))
 translate(plate == 0 ? [0.0, -384.0, 0] : [0,0,0])
  multmatrix([[0.0394260095, -0.999222493, 0.0, 308.44139], [0.999222493, 0.0394260095, 0.0, -163.33550400000001], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F5-A2L-knot-volume-2.stl", convexity=20);

// Plate 5: F5 A2L knot; volume 3; normal_part
if ((plate == 0 || plate == 5))
 translate(plate == 0 ? [0.0, -384.0, 0] : [0,0,0])
  multmatrix([[0.0394260095, -0.999222493, 0.0, 308.44139], [0.999222493, 0.0394260095, 0.0, -163.33550400000001], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F5-A2L-knot-volume-3.stl", convexity=20);

// Plate 5: F5 A2L knot; volume 4; normal_part
if ((plate == 0 || plate == 5))
 translate(plate == 0 ? [0.0, -384.0, 0] : [0,0,0])
  multmatrix([[0.0394260095, -0.999222493, 0.0, 308.44139], [0.999222493, 0.0394260095, 0.0, -163.33550400000001], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F5-A2L-knot-volume-4.stl", convexity=20);

// Plate 5: F5 A2L knot; volume 5; modifier_part
if ((plate == 0 || plate == 5) && show_modifiers)
 translate(plate == 0 ? [0.0, -384.0, 0] : [0,0,0])
  multmatrix([[0.0394260095, -0.999222493, 0.0, 308.44139], [0.999222493, 0.0394260095, 0.0, -163.33550400000001], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F5-A2L-knot-volume-5.stl", convexity=20);

// Plate 5: F5 A2L knot; volume 6; modifier_part
if ((plate == 0 || plate == 5) && show_modifiers)
 translate(plate == 0 ? [0.0, -384.0, 0] : [0,0,0])
  multmatrix([[0.0394260095, -0.999222493, 0.0, 308.44139], [0.999222493, 0.0394260095, 0.0, -163.33550400000001], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F5-A2L-knot-volume-6.stl", convexity=20);

// Plate 5: F5 A2L knot; volume 7; modifier_part
if ((plate == 0 || plate == 5) && show_modifiers)
 translate(plate == 0 ? [0.0, -384.0, 0] : [0,0,0])
  multmatrix([[0.0394260095, -0.999222493, 0.0, 308.44139], [0.999222493, 0.0394260095, 0.0, -163.33550400000001], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F5-A2L-knot-volume-7.stl", convexity=20);

// Plate 5: F5 A2L knot; volume 8; modifier_part
if ((plate == 0 || plate == 5) && show_modifiers)
 translate(plate == 0 ? [0.0, -384.0, 0] : [0,0,0])
  multmatrix([[0.0394260095, -0.999222493, 0.0, 308.44139], [0.999222493, 0.0394260095, 0.0, -163.33550400000001], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F5-A2L-knot-volume-8.stl", convexity=20);

// Plate 5: F5 A2L knot; volume 9; modifier_part
if ((plate == 0 || plate == 5) && show_modifiers)
 translate(plate == 0 ? [0.0, -384.0, 0] : [0,0,0])
  multmatrix([[0.0394260095, -0.999222493, 0.0, 308.44139], [0.999222493, 0.0394260095, 0.0, -163.33550400000001], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F5-A2L-knot-volume-9.stl", convexity=20);

// Plate 5: F5 A2L knot; volume 10; modifier_part
if ((plate == 0 || plate == 5) && show_modifiers)
 translate(plate == 0 ? [0.0, -384.0, 0] : [0,0,0])
  multmatrix([[0.0394260095, -0.999222493, 0.0, 308.44139], [0.999222493, 0.0394260095, 0.0, -163.33550400000001], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F5-A2L-knot-volume-10.stl", convexity=20);

// Plate 5: F5 A2L knot; volume 11; modifier_part
if ((plate == 0 || plate == 5) && show_modifiers)
 translate(plate == 0 ? [0.0, -384.0, 0] : [0,0,0])
  multmatrix([[0.0394260095, -0.999222493, 0.0, 308.44139], [0.999222493, 0.0394260095, 0.0, -163.33550400000001], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F5-A2L-knot-volume-11.stl", convexity=20);

// Plate 6: F6 A2L knot; volume 1; normal_part
if ((plate == 0 || plate == 6))
 translate(plate == 0 ? [396.0, -384.0, 0] : [0,0,0])
  multmatrix([[0.191586725, -0.981475688, 0.0, 150.617886], [0.981475688, 0.191586725, 0.0, 19.42829599999999], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F6-A2L-knot-volume-1.stl", convexity=20);

// Plate 6: F6 A2L knot; volume 2; normal_part
if ((plate == 0 || plate == 6))
 translate(plate == 0 ? [396.0, -384.0, 0] : [0,0,0])
  multmatrix([[0.191586725, -0.981475688, 0.0, 150.617886], [0.981475688, 0.191586725, 0.0, 19.42829599999999], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F6-A2L-knot-volume-2.stl", convexity=20);

// Plate 6: F6 A2L knot; volume 3; normal_part
if ((plate == 0 || plate == 6))
 translate(plate == 0 ? [396.0, -384.0, 0] : [0,0,0])
  multmatrix([[0.191586725, -0.981475688, 0.0, 150.617886], [0.981475688, 0.191586725, 0.0, 19.42829599999999], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F6-A2L-knot-volume-3.stl", convexity=20);

// Plate 6: F6 A2L knot; volume 4; modifier_part
if ((plate == 0 || plate == 6) && show_modifiers)
 translate(plate == 0 ? [396.0, -384.0, 0] : [0,0,0])
  multmatrix([[0.191586725, -0.981475688, 0.0, 150.617886], [0.981475688, 0.191586725, 0.0, 19.42829599999999], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F6-A2L-knot-volume-4.stl", convexity=20);

// Plate 6: F6 A2L knot; volume 5; modifier_part
if ((plate == 0 || plate == 6) && show_modifiers)
 translate(plate == 0 ? [396.0, -384.0, 0] : [0,0,0])
  multmatrix([[0.191586725, -0.981475688, 0.0, 150.617886], [0.981475688, 0.191586725, 0.0, 19.42829599999999], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F6-A2L-knot-volume-5.stl", convexity=20);

// Plate 6: F6 A2L knot; volume 6; modifier_part
if ((plate == 0 || plate == 6) && show_modifiers)
 translate(plate == 0 ? [396.0, -384.0, 0] : [0,0,0])
  multmatrix([[0.191586725, -0.981475688, 0.0, 150.617886], [0.981475688, 0.191586725, 0.0, 19.42829599999999], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F6-A2L-knot-volume-6.stl", convexity=20);

// Plate 6: F6 A2L knot; volume 7; modifier_part
if ((plate == 0 || plate == 6) && show_modifiers)
 translate(plate == 0 ? [396.0, -384.0, 0] : [0,0,0])
  multmatrix([[0.191586725, -0.981475688, 0.0, 150.617886], [0.981475688, 0.191586725, 0.0, 19.42829599999999], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F6-A2L-knot-volume-7.stl", convexity=20);

// Plate 7: F7 A2L knot; volume 1; normal_part
if ((plate == 0 || plate == 7))
 translate(plate == 0 ? [792.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.997944356, -0.0640863655, 0.0, 485.8473100000001], [0.0640863655, -0.997944356, 0.0, -1.7231689999999844], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F7-A2L-knot-volume-1.stl", convexity=20);

// Plate 7: F7 A2L knot; volume 2; normal_part
if ((plate == 0 || plate == 7))
 translate(plate == 0 ? [792.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.997944356, -0.0640863655, 0.0, 485.8473100000001], [0.0640863655, -0.997944356, 0.0, -1.7231689999999844], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F7-A2L-knot-volume-2.stl", convexity=20);

// Plate 7: F7 A2L knot; volume 3; normal_part
if ((plate == 0 || plate == 7))
 translate(plate == 0 ? [792.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.997944356, -0.0640863655, 0.0, 485.8473100000001], [0.0640863655, -0.997944356, 0.0, -1.7231689999999844], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F7-A2L-knot-volume-3.stl", convexity=20);

// Plate 7: F7 A2L knot; volume 4; normal_part
if ((plate == 0 || plate == 7))
 translate(plate == 0 ? [792.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.997944356, -0.0640863655, 0.0, 485.8473100000001], [0.0640863655, -0.997944356, 0.0, -1.7231689999999844], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F7-A2L-knot-volume-4.stl", convexity=20);

// Plate 7: F7 A2L knot; volume 5; modifier_part
if ((plate == 0 || plate == 7) && show_modifiers)
 translate(plate == 0 ? [792.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.997944356, -0.0640863655, 0.0, 485.8473100000001], [0.0640863655, -0.997944356, 0.0, -1.7231689999999844], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F7-A2L-knot-volume-5.stl", convexity=20);

// Plate 7: F7 A2L knot; volume 6; modifier_part
if ((plate == 0 || plate == 7) && show_modifiers)
 translate(plate == 0 ? [792.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.997944356, -0.0640863655, 0.0, 485.8473100000001], [0.0640863655, -0.997944356, 0.0, -1.7231689999999844], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F7-A2L-knot-volume-6.stl", convexity=20);

// Plate 7: F7 A2L knot; volume 7; modifier_part
if ((plate == 0 || plate == 7) && show_modifiers)
 translate(plate == 0 ? [792.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.997944356, -0.0640863655, 0.0, 485.8473100000001], [0.0640863655, -0.997944356, 0.0, -1.7231689999999844], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F7-A2L-knot-volume-7.stl", convexity=20);

// Plate 7: F7 A2L knot; volume 8; modifier_part
if ((plate == 0 || plate == 7) && show_modifiers)
 translate(plate == 0 ? [792.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.997944356, -0.0640863655, 0.0, 485.8473100000001], [0.0640863655, -0.997944356, 0.0, -1.7231689999999844], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F7-A2L-knot-volume-8.stl", convexity=20);

// Plate 7: F7 A2L knot; volume 9; modifier_part
if ((plate == 0 || plate == 7) && show_modifiers)
 translate(plate == 0 ? [792.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.997944356, -0.0640863655, 0.0, 485.8473100000001], [0.0640863655, -0.997944356, 0.0, -1.7231689999999844], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F7-A2L-knot-volume-9.stl", convexity=20);

// Plate 7: F7 A2L knot; volume 10; modifier_part
if ((plate == 0 || plate == 7) && show_modifiers)
 translate(plate == 0 ? [792.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.997944356, -0.0640863655, 0.0, 485.8473100000001], [0.0640863655, -0.997944356, 0.0, -1.7231689999999844], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F7-A2L-knot-volume-10.stl", convexity=20);

// Plate 7: F7 A2L knot; volume 11; modifier_part
if ((plate == 0 || plate == 7) && show_modifiers)
 translate(plate == 0 ? [792.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.997944356, -0.0640863655, 0.0, 485.8473100000001], [0.0640863655, -0.997944356, 0.0, -1.7231689999999844], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F7-A2L-knot-volume-11.stl", convexity=20);

// Plate 8: F8 A2L knot; volume 1; normal_part
if ((plate == 0 || plate == 8))
 translate(plate == 0 ? [1188.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.271260403, -0.962505997, 0.0, -103.38079999999991], [0.962505997, -0.271260403, 0.0, -46.560362], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F8-A2L-knot-volume-1.stl", convexity=20);

// Plate 8: F8 A2L knot; volume 2; normal_part
if ((plate == 0 || plate == 8))
 translate(plate == 0 ? [1188.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.271260403, -0.962505997, 0.0, -103.38079999999991], [0.962505997, -0.271260403, 0.0, -46.560362], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F8-A2L-knot-volume-2.stl", convexity=20);

// Plate 8: F8 A2L knot; volume 3; normal_part
if ((plate == 0 || plate == 8))
 translate(plate == 0 ? [1188.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.271260403, -0.962505997, 0.0, -103.38079999999991], [0.962505997, -0.271260403, 0.0, -46.560362], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F8-A2L-knot-volume-3.stl", convexity=20);

// Plate 8: F8 A2L knot; volume 4; normal_part
if ((plate == 0 || plate == 8))
 translate(plate == 0 ? [1188.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.271260403, -0.962505997, 0.0, -103.38079999999991], [0.962505997, -0.271260403, 0.0, -46.560362], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F8-A2L-knot-volume-4.stl", convexity=20);

// Plate 8: F8 A2L knot; volume 5; modifier_part
if ((plate == 0 || plate == 8) && show_modifiers)
 translate(plate == 0 ? [1188.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.271260403, -0.962505997, 0.0, -103.38079999999991], [0.962505997, -0.271260403, 0.0, -46.560362], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F8-A2L-knot-volume-5.stl", convexity=20);

// Plate 8: F8 A2L knot; volume 6; modifier_part
if ((plate == 0 || plate == 8) && show_modifiers)
 translate(plate == 0 ? [1188.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.271260403, -0.962505997, 0.0, -103.38079999999991], [0.962505997, -0.271260403, 0.0, -46.560362], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F8-A2L-knot-volume-6.stl", convexity=20);

// Plate 8: F8 A2L knot; volume 7; modifier_part
if ((plate == 0 || plate == 8) && show_modifiers)
 translate(plate == 0 ? [1188.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.271260403, -0.962505997, 0.0, -103.38079999999991], [0.962505997, -0.271260403, 0.0, -46.560362], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F8-A2L-knot-volume-7.stl", convexity=20);

// Plate 8: F8 A2L knot; volume 8; modifier_part
if ((plate == 0 || plate == 8) && show_modifiers)
 translate(plate == 0 ? [1188.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.271260403, -0.962505997, 0.0, -103.38079999999991], [0.962505997, -0.271260403, 0.0, -46.560362], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F8-A2L-knot-volume-8.stl", convexity=20);

// Plate 8: F8 A2L knot; volume 9; modifier_part
if ((plate == 0 || plate == 8) && show_modifiers)
 translate(plate == 0 ? [1188.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.271260403, -0.962505997, 0.0, -103.38079999999991], [0.962505997, -0.271260403, 0.0, -46.560362], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F8-A2L-knot-volume-9.stl", convexity=20);

// Plate 8: F8 A2L knot; volume 10; modifier_part
if ((plate == 0 || plate == 8) && show_modifiers)
 translate(plate == 0 ? [1188.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.271260403, -0.962505997, 0.0, -103.38079999999991], [0.962505997, -0.271260403, 0.0, -46.560362], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F8-A2L-knot-volume-10.stl", convexity=20);

// Plate 8: F8 A2L knot; volume 11; modifier_part
if ((plate == 0 || plate == 8) && show_modifiers)
 translate(plate == 0 ? [1188.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.271260403, -0.962505997, 0.0, -103.38079999999991], [0.962505997, -0.271260403, 0.0, -46.560362], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F8-A2L-knot-volume-11.stl", convexity=20);

// Plate 8: F8 A2L knot; volume 12; modifier_part
if ((plate == 0 || plate == 8) && show_modifiers)
 translate(plate == 0 ? [1188.0, -384.0, 0] : [0,0,0])
  multmatrix([[-0.271260403, -0.962505997, 0.0, -103.38079999999991], [0.962505997, -0.271260403, 0.0, -46.560362], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F8-A2L-knot-volume-12.stl", convexity=20);

// Plate 9: F9 A2L knot; volume 1; normal_part
if ((plate == 0 || plate == 9))
 translate(plate == 0 ? [0.0, -768.0, 0] : [0,0,0])
  multmatrix([[-0.949808544, -0.31283179, 0.0, -40.68005], [0.31283179, -0.949808544, 0.0, -100.33222], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F9-A2L-knot-volume-1.stl", convexity=20);

// Plate 9: F9 A2L knot; volume 2; normal_part
if ((plate == 0 || plate == 9))
 translate(plate == 0 ? [0.0, -768.0, 0] : [0,0,0])
  multmatrix([[-0.949808544, -0.31283179, 0.0, -40.68005], [0.31283179, -0.949808544, 0.0, -100.33222], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F9-A2L-knot-volume-2.stl", convexity=20);

// Plate 9: F9 A2L knot; volume 3; normal_part
if ((plate == 0 || plate == 9))
 translate(plate == 0 ? [0.0, -768.0, 0] : [0,0,0])
  multmatrix([[-0.949808544, -0.31283179, 0.0, -40.68005], [0.31283179, -0.949808544, 0.0, -100.33222], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F9-A2L-knot-volume-3.stl", convexity=20);

// Plate 9: F9 A2L knot; volume 4; normal_part
if ((plate == 0 || plate == 9))
 translate(plate == 0 ? [0.0, -768.0, 0] : [0,0,0])
  multmatrix([[-0.949808544, -0.31283179, 0.0, -40.68005], [0.31283179, -0.949808544, 0.0, -100.33222], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F9-A2L-knot-volume-4.stl", convexity=20);

// Plate 9: F9 A2L knot; volume 5; normal_part
if ((plate == 0 || plate == 9))
 translate(plate == 0 ? [0.0, -768.0, 0] : [0,0,0])
  multmatrix([[-0.949808544, -0.31283179, 0.0, -40.68005], [0.31283179, -0.949808544, 0.0, -100.33222], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F9-A2L-knot-volume-5.stl", convexity=20);

// Plate 9: F9 A2L knot; volume 6; modifier_part
if ((plate == 0 || plate == 9) && show_modifiers)
 translate(plate == 0 ? [0.0, -768.0, 0] : [0,0,0])
  multmatrix([[-0.949808544, -0.31283179, 0.0, -40.68005], [0.31283179, -0.949808544, 0.0, -100.33222], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F9-A2L-knot-volume-6.stl", convexity=20);

// Plate 9: F9 A2L knot; volume 7; modifier_part
if ((plate == 0 || plate == 9) && show_modifiers)
 translate(plate == 0 ? [0.0, -768.0, 0] : [0,0,0])
  multmatrix([[-0.949808544, -0.31283179, 0.0, -40.68005], [0.31283179, -0.949808544, 0.0, -100.33222], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F9-A2L-knot-volume-7.stl", convexity=20);

// Plate 9: F9 A2L knot; volume 8; modifier_part
if ((plate == 0 || plate == 9) && show_modifiers)
 translate(plate == 0 ? [0.0, -768.0, 0] : [0,0,0])
  multmatrix([[-0.949808544, -0.31283179, 0.0, -40.68005], [0.31283179, -0.949808544, 0.0, -100.33222], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F9-A2L-knot-volume-8.stl", convexity=20);

// Plate 9: F9 A2L knot; volume 9; modifier_part
if ((plate == 0 || plate == 9) && show_modifiers)
 translate(plate == 0 ? [0.0, -768.0, 0] : [0,0,0])
  multmatrix([[-0.949808544, -0.31283179, 0.0, -40.68005], [0.31283179, -0.949808544, 0.0, -100.33222], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F9-A2L-knot-volume-9.stl", convexity=20);

// Plate 9: F9 A2L knot; volume 10; modifier_part
if ((plate == 0 || plate == 9) && show_modifiers)
 translate(plate == 0 ? [0.0, -768.0, 0] : [0,0,0])
  multmatrix([[-0.949808544, -0.31283179, 0.0, -40.68005], [0.31283179, -0.949808544, 0.0, -100.33222], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F9-A2L-knot-volume-10.stl", convexity=20);

// Plate 9: F9 A2L knot; volume 11; modifier_part
if ((plate == 0 || plate == 9) && show_modifiers)
 translate(plate == 0 ? [0.0, -768.0, 0] : [0,0,0])
  multmatrix([[-0.949808544, -0.31283179, 0.0, -40.68005], [0.31283179, -0.949808544, 0.0, -100.33222], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F9-A2L-knot-volume-11.stl", convexity=20);

// Plate 9: F9 A2L knot; volume 12; modifier_part
if ((plate == 0 || plate == 9) && show_modifiers)
 translate(plate == 0 ? [0.0, -768.0, 0] : [0,0,0])
  multmatrix([[-0.949808544, -0.31283179, 0.0, -40.68005], [0.31283179, -0.949808544, 0.0, -100.33222], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F9-A2L-knot-volume-12.stl", convexity=20);

// Plate 9: F9 A2L knot; volume 13; modifier_part
if ((plate == 0 || plate == 9) && show_modifiers)
 translate(plate == 0 ? [0.0, -768.0, 0] : [0,0,0])
  multmatrix([[-0.949808544, -0.31283179, 0.0, -40.68005], [0.31283179, -0.949808544, 0.0, -100.33222], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F9-A2L-knot-volume-13.stl", convexity=20);

// Plate 10: F10 A2L knot; volume 1; normal_part
if ((plate == 0 || plate == 10))
 translate(plate == 0 ? [396.0, -768.0, 0] : [0,0,0])
  multmatrix([[0.997912921, -0.0645740023, 0.0, 485.79029], [0.0645740023, 0.997912921, 0.0, 321.847285], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F10-A2L-knot-volume-1.stl", convexity=20);

// Plate 10: F10 A2L knot; volume 2; normal_part
if ((plate == 0 || plate == 10))
 translate(plate == 0 ? [396.0, -768.0, 0] : [0,0,0])
  multmatrix([[0.997912921, -0.0645740023, 0.0, 485.79029], [0.0645740023, 0.997912921, 0.0, 321.847285], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F10-A2L-knot-volume-2.stl", convexity=20);

// Plate 10: F10 A2L knot; volume 3; normal_part
if ((plate == 0 || plate == 10))
 translate(plate == 0 ? [396.0, -768.0, 0] : [0,0,0])
  multmatrix([[0.997912921, -0.0645740023, 0.0, 485.79029], [0.0645740023, 0.997912921, 0.0, 321.847285], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F10-A2L-knot-volume-3.stl", convexity=20);

// Plate 10: F10 A2L knot; volume 4; normal_part
if ((plate == 0 || plate == 10))
 translate(plate == 0 ? [396.0, -768.0, 0] : [0,0,0])
  multmatrix([[0.997912921, -0.0645740023, 0.0, 485.79029], [0.0645740023, 0.997912921, 0.0, 321.847285], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Knot STL/F10-A2L-knot-volume-4.stl", convexity=20);

// Plate 10: F10 A2L knot; volume 5; modifier_part
if ((plate == 0 || plate == 10) && show_modifiers)
 translate(plate == 0 ? [396.0, -768.0, 0] : [0,0,0])
  multmatrix([[0.997912921, -0.0645740023, 0.0, 485.79029], [0.0645740023, 0.997912921, 0.0, 321.847285], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F10-A2L-knot-volume-5.stl", convexity=20);

// Plate 10: F10 A2L knot; volume 6; modifier_part
if ((plate == 0 || plate == 10) && show_modifiers)
 translate(plate == 0 ? [396.0, -768.0, 0] : [0,0,0])
  multmatrix([[0.997912921, -0.0645740023, 0.0, 485.79029], [0.0645740023, 0.997912921, 0.0, 321.847285], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F10-A2L-knot-volume-6.stl", convexity=20);

// Plate 10: F10 A2L knot; volume 7; modifier_part
if ((plate == 0 || plate == 10) && show_modifiers)
 translate(plate == 0 ? [396.0, -768.0, 0] : [0,0,0])
  multmatrix([[0.997912921, -0.0645740023, 0.0, 485.79029], [0.0645740023, 0.997912921, 0.0, 321.847285], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F10-A2L-knot-volume-7.stl", convexity=20);

// Plate 10: F10 A2L knot; volume 8; modifier_part
if ((plate == 0 || plate == 10) && show_modifiers)
 translate(plate == 0 ? [396.0, -768.0, 0] : [0,0,0])
  multmatrix([[0.997912921, -0.0645740023, 0.0, 485.79029], [0.0645740023, 0.997912921, 0.0, 321.847285], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F10-A2L-knot-volume-8.stl", convexity=20);

// Plate 10: F10 A2L knot; volume 9; modifier_part
if ((plate == 0 || plate == 10) && show_modifiers)
 translate(plate == 0 ? [396.0, -768.0, 0] : [0,0,0])
  multmatrix([[0.997912921, -0.0645740023, 0.0, 485.79029], [0.0645740023, 0.997912921, 0.0, 321.847285], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F10-A2L-knot-volume-9.stl", convexity=20);

// Plate 10: F10 A2L knot; volume 10; modifier_part
if ((plate == 0 || plate == 10) && show_modifiers)
 translate(plate == 0 ? [396.0, -768.0, 0] : [0,0,0])
  multmatrix([[0.997912921, -0.0645740023, 0.0, 485.79029], [0.0645740023, 0.997912921, 0.0, 321.847285], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F10-A2L-knot-volume-10.stl", convexity=20);

// Plate 10: F10 A2L knot; volume 11; modifier_part
if ((plate == 0 || plate == 10) && show_modifiers)
 translate(plate == 0 ? [396.0, -768.0, 0] : [0,0,0])
  multmatrix([[0.997912921, -0.0645740023, 0.0, 485.79029], [0.0645740023, 0.997912921, 0.0, 321.847285], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Knot STL/F10-A2L-knot-volume-11.stl", convexity=20);
