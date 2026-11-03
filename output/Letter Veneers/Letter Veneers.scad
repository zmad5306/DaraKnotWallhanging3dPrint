// Exact mesh-based CAD snapshot of Letter Veneers.3mf.
// Uses the supplied STL volumes; this is not a parametric feature history.
// Dimensions, material regions, print poses and modifiers come from the saved project.
plate = 1; // Select the plate to inspect. 0 shows all plates.
show_modifiers = false;

// Plate 1: Left letter veneer; volume 1; normal_part
if ((plate == 0 || plate == 1))
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 162.423573], [0.0, 1.0, 0.0, 160.075043], [0.0, 0.0, 1.0, 148.66925], [0.0, 0.0, 0.0, 1.0]])
   color("#B87333") import("Letter Veneers STL/Left-letter-veneer-volume-1.stl", convexity=20);

// Plate 2: Right letter veneer; volume 1; normal_part
if ((plate == 0 || plate == 2))
 translate(plate == 0 ? [396.0, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 162.42341199999998], [0.0, 1.0, 0.0, 160.0], [0.0, 0.0, 1.0, 148.674362], [0.0, 0.0, 0.0, 1.0]])
   color("#B87333") import("Letter Veneers STL/Right-letter-veneer-volume-1.stl", convexity=20);

// Plate 3: Center letter veneer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [0.0, -384.0, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 162.423569], [0.0, 1.0, 0.0, 159.999992], [0.0, 0.0, 1.0, 148.674362], [0.0, 0.0, 0.0, 1.0]])
   color("#B87333") import("Letter Veneers STL/Center-letter-veneer-volume-1.stl", convexity=20);
