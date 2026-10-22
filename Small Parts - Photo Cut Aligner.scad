// Exact mesh-based CAD snapshot of Small Parts - Photo Cut Aligner.3mf.
// Uses the supplied STL volumes; this is not a parametric feature history.
// Dimensions, material regions, print poses and modifiers come from the saved project.
plate = 1; // Select the plate to inspect. 0 shows all plates.
show_modifiers = false;

// Plate 1: Backer 2 - honeycomb tracing - 2mm; volume 1; normal_part
if ((plate == 0 || plate == 1))
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 120.966439], [0.0, 1.0, 0.0, 132.74541], [0.0, 0.0, 1.0, 1.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts - Photo Cut Aligner STL/Backer-2---honeycomb-tracing---2mm-volume-1.stl", convexity=20);
