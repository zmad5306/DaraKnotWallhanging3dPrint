// Exact mesh-based CAD snapshot of Small Parts.3mf.
// Uses the supplied STL volumes; this is not a parametric feature history.
// Dimensions, material regions, print poses and modifiers come from the saved project.
plate = 1; // Select the plate to inspect. 0 shows all plates.
show_modifiers = false;

// Plate 1: Backer3; volume 1; normal_part
if ((plate == 0 || plate == 1))
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 64.2532082], [0.0, 1.0, 0.0, 64.390892], [0.0, 0.0, 1.0, 0.800000012], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/Backer3-volume-1.stl", convexity=20);

// Plate 1: Backer1; volume 1; normal_part
if ((plate == 0 || plate == 1))
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 191.656006], [0.0, 1.0, 0.0, 64.2017784], [0.0, 0.0, 1.0, 0.800000012], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/Backer1-volume-1.stl", convexity=20);

// Plate 1: Backer5; volume 1; normal_part
if ((plate == 0 || plate == 1))
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 64.2546234], [0.0, 1.0, 0.0, 191.744667], [0.0, 0.0, 1.0, 0.800000012], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/Backer5-volume-1.stl", convexity=20);

// Plate 1: Backer7; volume 1; normal_part
if ((plate == 0 || plate == 1))
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 191.7407], [0.0, 1.0, 0.0, 191.610268], [0.0, 0.0, 1.0, 0.800000012], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/Backer7-volume-1.stl", convexity=20);

// Plate 2: Backer4; volume 1; normal_part
if ((plate == 0 || plate == 2))
 translate(plate == 0 ? [307.2, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 64.30598500000002], [0.0, 1.0, 0.0, 64.3030815], [0.0, 0.0, 1.0, 0.800000012], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/Backer4-volume-1.stl", convexity=20);

// Plate 2: Backer2; volume 1; normal_part
if ((plate == 0 || plate == 2))
 translate(plate == 0 ? [307.2, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 191.751308], [0.0, 1.0, 0.0, 64.3872147], [0.0, 0.0, 1.0, 0.800000012], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/Backer2-volume-1.stl", convexity=20);

// Plate 2: Backer6; volume 1; normal_part
if ((plate == 0 || plate == 2))
 translate(plate == 0 ? [307.2, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 64.25347900000003], [0.0, 1.0, 0.0, 191.610619], [0.0, 0.0, 1.0, 0.800000012], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/Backer6-volume-1.stl", convexity=20);

// Plate 2: Backer8; volume 1; normal_part
if ((plate == 0 || plate == 2))
 translate(plate == 0 ? [307.2, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 191.61962900000003], [0.0, 1.0, 0.0, 191.791801], [0.0, 0.0, 1.0, 0.800000012], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/Backer8-volume-1.stl", convexity=20);

// Plate 3: B1 A1 companion wall block; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 84.0], [0.0, 1.0, 0.0, 55.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/B1-A1-companion-wall-block-volume-1.stl", convexity=20);

// Plate 3: B1 A1 companion wall block; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 84.0], [0.0, 1.0, 0.0, 55.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/B1-A1-companion-wall-block-volume-2.stl", convexity=20);

// Plate 3: B1 A1 companion wall block; volume 3; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 84.0], [0.0, 1.0, 0.0, 55.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/B1-A1-companion-wall-block-volume-3.stl", convexity=20);

// Plate 3: B1 A1 companion wall block; volume 4; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 84.0], [0.0, 1.0, 0.0, 55.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/B1-A1-companion-wall-block-volume-4.stl", convexity=20);

// Plate 3: B2 A1 companion wall block; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 84.0], [0.0, 1.0, 0.0, 103.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/B2-A1-companion-wall-block-volume-1.stl", convexity=20);

// Plate 3: B2 A1 companion wall block; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 84.0], [0.0, 1.0, 0.0, 103.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/B2-A1-companion-wall-block-volume-2.stl", convexity=20);

// Plate 3: B2 A1 companion wall block; volume 3; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 84.0], [0.0, 1.0, 0.0, 103.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/B2-A1-companion-wall-block-volume-3.stl", convexity=20);

// Plate 3: B2 A1 companion wall block; volume 4; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 84.0], [0.0, 1.0, 0.0, 103.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/B2-A1-companion-wall-block-volume-4.stl", convexity=20);

// Plate 3: B3 A1 companion wall block; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 84.0], [0.0, 1.0, 0.0, 151.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/B3-A1-companion-wall-block-volume-1.stl", convexity=20);

// Plate 3: B3 A1 companion wall block; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 84.0], [0.0, 1.0, 0.0, 151.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/B3-A1-companion-wall-block-volume-2.stl", convexity=20);

// Plate 3: B3 A1 companion wall block; volume 3; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 84.0], [0.0, 1.0, 0.0, 151.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/B3-A1-companion-wall-block-volume-3.stl", convexity=20);

// Plate 3: B3 A1 companion wall block; volume 4; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 84.0], [0.0, 1.0, 0.0, 151.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/B1-A1-companion-wall-block-volume-4.stl", convexity=20);

// Plate 3: B4 A1 companion wall block; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 84.0], [0.0, 1.0, 0.0, 199.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/B4-A1-companion-wall-block-volume-1.stl", convexity=20);

// Plate 3: B4 A1 companion wall block; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 84.0], [0.0, 1.0, 0.0, 199.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/B4-A1-companion-wall-block-volume-2.stl", convexity=20);

// Plate 3: B4 A1 companion wall block; volume 3; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 84.0], [0.0, 1.0, 0.0, 199.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/B4-A1-companion-wall-block-volume-3.stl", convexity=20);

// Plate 3: B4 A1 companion wall block; volume 4; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 84.0], [0.0, 1.0, 0.0, 199.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/B2-A1-companion-wall-block-volume-4.stl", convexity=20);

// Plate 3: R1 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 48.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R1 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 48.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R2 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 48.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R2 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 48.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R3 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 231.0], [0.0, 1.0, 0.0, 48.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R3 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 231.0], [0.0, 1.0, 0.0, 48.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R4 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 64.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R4 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 64.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R5 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 64.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R5 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 64.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R6 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 231.0], [0.0, 1.0, 0.0, 64.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R6 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 231.0], [0.0, 1.0, 0.0, 64.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R7 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 80.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R7 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 80.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R8 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 80.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R8 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 80.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R9 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 231.0], [0.0, 1.0, 0.0, 80.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R9 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 231.0], [0.0, 1.0, 0.0, 80.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R10 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 96.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R10 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 96.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R11 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 96.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R11 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 96.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R12 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 231.0], [0.0, 1.0, 0.0, 96.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R12 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 231.0], [0.0, 1.0, 0.0, 96.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R13 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 112.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R13 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 112.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R14 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 112.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R14 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 112.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R15 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 231.0], [0.0, 1.0, 0.0, 112.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R15 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 231.0], [0.0, 1.0, 0.0, 112.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R16 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 128.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R16 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 128.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R17 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 128.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R17 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 128.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R18 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 231.0], [0.0, 1.0, 0.0, 128.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R18 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 231.0], [0.0, 1.0, 0.0, 128.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R19 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 144.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R19 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 144.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R20 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 144.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R20 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 144.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R21 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 231.0], [0.0, 1.0, 0.0, 144.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R21 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 231.0], [0.0, 1.0, 0.0, 144.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R22 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 160.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R22 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 160.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R23 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 160.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R23 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 160.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R24 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 231.0], [0.0, 1.0, 0.0, 160.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R24 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 231.0], [0.0, 1.0, 0.0, 160.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R25 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 176.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R25 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 176.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R26 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 176.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R26 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 176.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R27 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 231.0], [0.0, 1.0, 0.0, 176.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R27 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 231.0], [0.0, 1.0, 0.0, 176.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R28 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 192.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R28 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 192.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R29 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 192.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R29 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 192.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R30 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 231.0], [0.0, 1.0, 0.0, 192.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R30 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 231.0], [0.0, 1.0, 0.0, 192.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R31 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 208.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R31 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 208.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 3: R32 photo retainer; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 208.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1-photo-retainer-volume-1.stl", convexity=20);

// Plate 3: R32 photo retainer; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [614.4, 0.0, 0] : [0,0,0])
  multmatrix([[1.0, -0.0, 0.0, 205.0], [0.0, 1.0, 0.0, 208.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Small Parts STL/R1-photo-retainer-volume-2.stl", convexity=20);

// Plate 4: V - crotch datum - V3 alignment shoe r3; volume 1; normal_part
if ((plate == 0 || plate == 4))
 translate(plate == 0 ? [0.0, -307.2, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 70.0000009], [0.0, 1.0, 0.0, 105.00000699999998], [0.0, 0.0, 1.0, 10.3000002], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/V---crotch-datum---V3-alignment-shoe-r3-volume-1.stl", convexity=20);

// Plate 4: B - stem bottom - V3 alignment shoe r3; volume 1; normal_part
if ((plate == 0 || plate == 4))
 translate(plate == 0 ? [0.0, -307.2, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 170.0], [0.0, 1.0, 0.0, 128.0], [0.0, 0.0, 1.0, 10.3000002], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/B---stem-bottom---V3-alignment-shoe-r3-volume-1.stl", convexity=20);

// Plate 5: L1 - left upper curve - V1 alignment r1; volume 1; normal_part
if ((plate == 0 || plate == 5))
 translate(plate == 0 ? [307.2, -307.2, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 67.99999700000001], [0.0, 1.0, 0.0, 180.0], [0.0, 0.0, 1.0, 10.3000002], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/L1---left-upper-curve---V1-alignment-r1-volume-1.stl", convexity=20);

// Plate 5: L2 - left lower end - V1 alignment r1; volume 1; normal_part
if ((plate == 0 || plate == 5))
 translate(plate == 0 ? [307.2, -307.2, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 55.0], [0.0, 1.0, 0.0, 86.0], [0.0, 0.0, 1.0, 10.3000002], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/L2---left-lower-end---V1-alignment-r1-volume-1.stl", convexity=20);

// Plate 5: R1 - right upper curve - V2 alignment r1; volume 1; normal_part
if ((plate == 0 || plate == 5))
 translate(plate == 0 ? [307.2, -307.2, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 179.0], [0.0, 1.0, 0.0, 180.0], [0.0, 0.0, 1.0, 10.3000002], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R1---right-upper-curve---V2-alignment-r1-volume-1.stl", convexity=20);

// Plate 5: R2 - right lower end - V2 alignment r1; volume 1; normal_part
if ((plate == 0 || plate == 5))
 translate(plate == 0 ? [307.2, -307.2, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 168.000004], [0.0, 1.0, 0.0, 86.0], [0.0, 0.0, 1.0, 10.3000002], [0.0, 0.0, 0.0, 1.0]])
   color("#FFFFFF") import("Small Parts STL/R2---right-lower-end---V2-alignment-r1-volume-1.stl", convexity=20);
