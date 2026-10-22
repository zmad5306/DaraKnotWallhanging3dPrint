// Exact mesh-based CAD snapshot of Small Parts - Crate Stencils.3mf.
// Uses the supplied STL volumes; this is not a parametric feature history.
// Dimensions, material regions, print poses and modifiers come from the saved project.
plate = 1; // Select the plate to inspect. 0 shows all plates.
show_modifiers = false;

// Plate 1: 01-THIS-END-UP-1-of-3; volume 1; normal_part
if ((plate == 0 || plate == 1))
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 128.0], [0.0, 1.0, 0.0, 128.0], [0.0, 0.0, 1.0, 0.400000006], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts - Crate Stencils STL/01-THIS-END-UP-1-of-3-volume-1.stl", convexity=20);

// Plate 2: 02-THIS-END-UP-2-of-3; volume 1; normal_part
if ((plate == 0 || plate == 2))
 translate(plate == 0 ? [307.2, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 128.0], [0.0, 1.0, 0.0, 128.0], [0.0, 0.0, 1.0, 0.400000006], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts - Crate Stencils STL/02-THIS-END-UP-2-of-3-volume-1.stl", convexity=20);

// Plate 3: 03-THIS-END-UP-3-of-3; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 128.0], [0.0, 1.0, 0.0, 128.0], [0.0, 0.0, 1.0, 0.400000006], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts - Crate Stencils STL/03-THIS-END-UP-3-of-3-volume-1.stl", convexity=20);

// Plate 4: 04-FRAGILE-1-of-3; volume 1; normal_part
if ((plate == 0 || plate == 4))
 translate(plate == 0 ? [0.0, -307.2, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 128.0], [0.0, 1.0, 0.0, 128.0], [0.0, 0.0, 1.0, 0.400000006], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts - Crate Stencils STL/04-FRAGILE-1-of-3-volume-1.stl", convexity=20);

// Plate 5: 05-FRAGILE-2-of-3; volume 1; normal_part
if ((plate == 0 || plate == 5))
 translate(plate == 0 ? [307.2, -307.2, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 128.0], [0.0, 1.0, 0.0, 128.0], [0.0, 0.0, 1.0, 0.400000006], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts - Crate Stencils STL/05-FRAGILE-2-of-3-volume-1.stl", convexity=20);

// Plate 6: 06-FRAGILE-3-of-3; volume 1; normal_part
if ((plate == 0 || plate == 6))
 translate(plate == 0 ? [614.4, -307.2, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 128.0], [0.0, 1.0, 0.0, 128.0], [0.0, 0.0, 1.0, 0.400000006], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts - Crate Stencils STL/06-FRAGILE-3-of-3-volume-1.stl", convexity=20);
