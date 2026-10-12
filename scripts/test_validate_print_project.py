"""Regression checks for compact decimal G-code and conservative arc bounds."""
import unittest

from validate_print_project import scan_gcode, filament_weights


class GcodeBoundsTests(unittest.TestCase):
    def test_multicolor_mass_includes_every_filament(self):
        self.assertEqual(filament_weights('; total filament weight [g] : 101.82, 8.71, 0.00\n'), [101.82, 8.71, 0.0])
        self.assertEqual(filament_weights('; total filament weight [g] : 150,34\n; filament: 1,3\n'), [150, 0, 34])
        self.assertEqual(filament_weights('; total filament weight [g] : 60\n; filament: 3\n'), [0, 0, 60])

    def test_compact_decimals_and_width(self):
        result = scan_gcode('M83\nG1 X.5 Y1\n; FEATURE: Outer wall\n; LINE_WIDTH: 0.4\nG1 X2 Y1 E.123\n')
        self.assertEqual(result['extrusion_moves_checked'], 1)
        self.assertAlmostEqual(result['conservative_bed_edge_clearance_mm'], .3)

    def test_negative_compact_coordinate_is_outside_bed(self):
        result = scan_gcode('M83\nG1 X1 Y1\n; FEATURE: Brim\nG1 X-.5 Y1 E+.1\n')
        self.assertLess(result['conservative_bed_edge_clearance_mm'], 0)

    def test_absolute_e_and_reset_exclude_retractions(self):
        result = scan_gcode('M82\nG1 X1 Y1\nG92 E10\n; FEATURE: Outer wall\nG1 X2 E10.1\nG1 X3 E9\nG92 E0\nG1 X4 E.1\n')
        self.assertEqual(result['extrusion_moves_checked'], 2)

    def test_arc_extremum_exceeds_endpoint_bounds(self):
        result = scan_gcode('M83\nG1 X1 Y1\n; FEATURE: Outer wall\nG2 X2 Y1 I.5 J0 E.1\n')
        self.assertAlmostEqual(result['extruding_xy_bounds_mm'][1][1], 1.5)

    def test_relative_motion_and_custom_purge(self):
        result = scan_gcode('M83\nG1 X-20 Y1 E5\nG90\nG1 X2 Y2\n; FEATURE: Outer wall\nG91\nG1 X.5 Y.5 E.1\n')
        self.assertEqual(result['extruding_xy_bounds_mm'], [[2, 2], [2.5, 2.5]])


if __name__ == '__main__':
    unittest.main()
