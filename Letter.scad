// Exact mesh-based CAD snapshot of Letter.3mf.
// Uses the supplied STL volumes; this is not a parametric feature history.
// Dimensions, material regions, print poses and modifiers come from the saved project.
plate = 1; // Select the plate to inspect. 0 shows all plates.
show_modifiers = false;

// Plate 1: C1 A2L flat M core; volume 1; normal_part
if ((plate == 0 || plate == 1))
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.910426725, -0.413670374, 0.0, 302.579304], [0.413670374, 0.910426725, 0.0, 172.286024], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#B87333") import("Letter STL/C1-A2L-flat-M-core-volume-1.stl", convexity=20);

// Plate 1: C1 A2L flat M core; volume 2; modifier_part
if ((plate == 0 || plate == 1) && show_modifiers)
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.910426725, -0.413670374, 0.0, 302.579304], [0.413670374, 0.910426725, 0.0, 172.286024], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Letter STL/C1-A2L-flat-M-core-volume-2.stl", convexity=20);

// Plate 1: C1 A2L flat M core; volume 3; modifier_part
if ((plate == 0 || plate == 1) && show_modifiers)
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.910426725, -0.413670374, 0.0, 302.579304], [0.413670374, 0.910426725, 0.0, 172.286024], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Letter STL/C1-A2L-flat-M-core-volume-3.stl", convexity=20);

// Plate 1: C1 A2L flat M core; volume 4; modifier_part
if ((plate == 0 || plate == 1) && show_modifiers)
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.910426725, -0.413670374, 0.0, 302.579304], [0.413670374, 0.910426725, 0.0, 172.286024], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Letter STL/C1-A2L-flat-M-core-volume-4.stl", convexity=20);

// Plate 1: C1 A2L flat M core; volume 5; modifier_part
if ((plate == 0 || plate == 1) && show_modifiers)
 translate(plate == 0 ? [0.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.910426725, -0.413670374, 0.0, 302.579304], [0.413670374, 0.910426725, 0.0, 172.286024], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Letter STL/C1-A2L-flat-M-core-volume-5.stl", convexity=20);

// Plate 2: C2 A2L flat M core; volume 1; normal_part
if ((plate == 0 || plate == 2))
 translate(plate == 0 ? [396.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.301481622, -0.953471988, 0.0, 169.874725], [0.953471988, 0.301481622, 0.0, -5.43034899999998], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#B87333") import("Letter STL/C2-A2L-flat-M-core-volume-1.stl", convexity=20);

// Plate 2: C2 A2L flat M core; volume 2; modifier_part
if ((plate == 0 || plate == 2) && show_modifiers)
 translate(plate == 0 ? [396.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.301481622, -0.953471988, 0.0, 169.874725], [0.953471988, 0.301481622, 0.0, -5.43034899999998], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Letter STL/C2-A2L-flat-M-core-volume-2.stl", convexity=20);

// Plate 2: C2 A2L flat M core; volume 3; modifier_part
if ((plate == 0 || plate == 2) && show_modifiers)
 translate(plate == 0 ? [396.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.301481622, -0.953471988, 0.0, 169.874725], [0.953471988, 0.301481622, 0.0, -5.43034899999998], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Letter STL/C2-A2L-flat-M-core-volume-3.stl", convexity=20);

// Plate 2: C2 A2L flat M core; volume 4; modifier_part
if ((plate == 0 || plate == 2) && show_modifiers)
 translate(plate == 0 ? [396.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.301481622, -0.953471988, 0.0, 169.874725], [0.953471988, 0.301481622, 0.0, -5.43034899999998], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Letter STL/C2-A2L-flat-M-core-volume-4.stl", convexity=20);

// Plate 3: C3 A2L flat M core; volume 1; normal_part
if ((plate == 0 || plate == 3))
 translate(plate == 0 ? [792.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.684815835, -0.728716181, 0.0, 114.42772500000001], [0.728716181, 0.684815835, 0.0, 215.084733], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#B87333") import("Letter STL/C3-A2L-flat-M-core-volume-1.stl", convexity=20);

// Plate 3: C3 A2L flat M core; volume 2; modifier_part
if ((plate == 0 || plate == 3) && show_modifiers)
 translate(plate == 0 ? [792.0, 0.0, 0] : [0,0,0])
  multmatrix([[0.684815835, -0.728716181, 0.0, 114.42772500000001], [0.728716181, 0.684815835, 0.0, 215.084733], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Letter STL/C3-A2L-flat-M-core-volume-2.stl", convexity=20);

// Plate 4: C4 A2L flat M core; volume 1; normal_part
if ((plate == 0 || plate == 4))
 translate(plate == 0 ? [0.0, -384.0, 0] : [0,0,0])
  multmatrix([[6.123234e-17, -1.0, 0.0, -9.36774999999989], [1.0, 6.123234e-17, 0.0, 367.102341], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#B87333") import("Letter STL/C4-A2L-flat-M-core-volume-1.stl", convexity=20);

// Plate 4: C4 A2L flat M core; volume 2; modifier_part
if ((plate == 0 || plate == 4) && show_modifiers)
 translate(plate == 0 ? [0.0, -384.0, 0] : [0,0,0])
  multmatrix([[6.123234e-17, -1.0, 0.0, -9.36774999999989], [1.0, 6.123234e-17, 0.0, 367.102341], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Letter STL/C4-A2L-flat-M-core-volume-2.stl", convexity=20);

// Plate 4: C5 A2L flat M core; volume 1; normal_part
if ((plate == 0 || plate == 4))
 translate(plate == 0 ? [0.0, -384.0, 0] : [0,0,0])
  multmatrix([[6.123234e-17, -1.0, 0.0, 138.0], [1.0, 6.123234e-17, 0.0, -43.31073600000002], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#B87333") import("Letter STL/C5-A2L-flat-M-core-volume-1.stl", convexity=20);

// Plate 4: C5 A2L flat M core; volume 2; modifier_part
if ((plate == 0 || plate == 4) && show_modifiers)
 translate(plate == 0 ? [0.0, -384.0, 0] : [0,0,0])
  multmatrix([[6.123234e-17, -1.0, 0.0, 138.0], [1.0, 6.123234e-17, 0.0, -43.31073600000002], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
   color("#FF00FF") import("Letter STL/C5-A2L-flat-M-core-volume-2.stl", convexity=20);

// Plate 5: V1 A2L hammered veneer and wall cradle r6 end ties; volume 1; normal_part
if ((plate == 0 || plate == 5))
 translate(plate == 0 ? [396.0, -384.0, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 165.0], [0.0, 1.0, 0.0, 160.0], [0.0, 0.0, 1.0, 148.66925], [0.0, 0.0, 0.0, 1.0]])
   color("#B87333") import("Letter STL/V1-A2L-hammered-veneer-and-wall-cradle-r6-end-ties-volume-1.stl", convexity=20);

// Plate 6: V2 A2L hammered veneer and wall cradle r6 end ties; volume 1; normal_part
if ((plate == 0 || plate == 6))
 translate(plate == 0 ? [792.0, -384.0, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 165.0], [0.0, 1.0, 0.0, 160.0], [0.0, 0.0, 1.0, 148.674362], [0.0, 0.0, 0.0, 1.0]])
   color("#B87333") import("Letter STL/V2-A2L-hammered-veneer-and-wall-cradle-r6-end-ties-volume-1.stl", convexity=20);

// Plate 7: V3 A2L hammered veneer and wall cradle r6 end ties; volume 1; normal_part
if ((plate == 0 || plate == 7))
 translate(plate == 0 ? [0.0, -768.0, 0] : [0,0,0])
  multmatrix([[1.0, 0.0, 0.0, 165.0], [0.0, 1.0, 0.0, 160.0], [0.0, 0.0, 1.0, 148.674362], [0.0, 0.0, 0.0, 1.0]])
   color("#B87333") import("Letter STL/V3-A2L-hammered-veneer-and-wall-cradle-r6-end-ties-volume-1.stl", convexity=20);
