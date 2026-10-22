// Exact mesh-based CAD snapshot of Small Parts - Sanding Block PLA.3mf.
// Uses the supplied STL volumes; this is not a parametric feature history.
// Dimensions, material regions, print poses and modifiers come from the saved project.
plate = 1; // Select the plate to inspect. 0 shows all plates.
show_modifiers = false;

// Plate 1: Lock - quarter sheet; volume 1; normal_part
if ((plate == 0 || plate == 1))
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.000246403085, 0.999993842, 0.00350066719, 168.998713], [-0.0702133129, 0.00350932831, -0.997525827, 164.366737], [-0.99753197, 4.41866435e-17, 0.0702137453, 17.5130492], [0.0, 0.0, 0.0, 1.0]])
   color("#0000FF") import("Small Parts - Sanding Block PLA STL/Lock---quarter-sheet-volume-1.stl", convexity=20);

// Plate 1: Screw - quarter sheet; volume 1; normal_part
if ((plate == 0 || plate == 1))
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[-0.907804934, 8.36592171e-06, -0.41939266, 202.960018], [5.71036603e-06, 1.0, 7.58721733e-06, 64.999925], [0.41939266, 4.49282772e-06, -0.907804934, 14.4573278], [0.0, 0.0, 0.0, 1.0]])
   color("#0000FF") import("Small Parts - Sanding Block PLA STL/Screw---quarter-sheet-volume-1.stl", convexity=20);

// Plate 1: Base - quarter sheet; volume 1; normal_part
if ((plate == 0 || plate == 1))
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[-2.22044605e-16, -1.0, 0.0, 70.0], [1.0, -2.22044605e-16, 0.0, 75.0], [0.0, 0.0, 1.0, 21.1012001], [0.0, 0.0, 0.0, 1.0]])
   color("#0000FF") import("Small Parts - Sanding Block PLA STL/Base---quarter-sheet-volume-1.stl", convexity=20);

// Plate 1: Tighteneer - quarter sheet; volume 1; normal_part
if ((plate == 0 || plate == 1))
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[-7.59437199e-17, -1.0, -2.0865368e-16, 70.0], [0.342020109, -2.22044605e-16, 0.939692633, 161.722056], [-0.939692633, -1.11698179e-25, 0.342020109, 17.3716338], [0.0, 0.0, 0.0, 1.0]])
   color("#0000FF") import("Small Parts - Sanding Block PLA STL/Tighteneer---quarter-sheet-volume-1.stl", convexity=20);

// Plate 1: Nut - quarter sheet; volume 1; normal_part
if ((plate == 0 || plate == 1))
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[2.22044605e-16, 0.0, 1.0, 147.0], [0.0, 1.0, 0.0, 65.0], [-1.0, 0.0, 2.22044605e-16, 7.03384638], [0.0, 0.0, 0.0, 1.0]])
   color("#0000FF") import("Small Parts - Sanding Block PLA STL/Nut---quarter-sheet-volume-1.stl", convexity=20);
