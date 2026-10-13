"""Tests for the independent cosmetic review's screening and motion reader."""
import unittest
from review_curve_artifacts import curve_candidates, surface_paths, arc_samples
import numpy as np
from shapely.geometry import Point, Polygon


class CurveReviewTests(unittest.TestCase):
    def test_round_curve_and_designed_corners_are_not_isolated_kinks(self):
        self.assertEqual(curve_candidates(Point(0,0).buffer(100,quad_segs=128))[0], [])
        self.assertEqual(curve_candidates(Polygon([(0,0),(40,0),(40,40),(0,40)]))[0], [])

    def test_local_bump_on_gentle_edge_is_flagged(self):
        polygon=Polygon([(0,0),(20,0),(22,.3),(24,0),(44,0),(44,-20),(0,-20)])
        candidates,_=curve_candidates(polygon)
        self.assertTrue(any(19 <= r['assembly_xy_mm'][0] <= 24 for r in candidates))

    def test_arc_samples_follow_major_arc_not_endpoint_chord(self):
        xy=arc_samples((1,0),(0,-1),{'I':-1,'J':0},True)
        np.testing.assert_allclose(np.linalg.norm(xy,axis=1),1,atol=1e-10)
        self.assertLess(xy[:,0].min(),-.99)
        self.assertGreater(xy[:,1].max(),.99)

    def test_motion_modes_skip_custom_travel_and_retraction(self):
        gcode='''G90
M83
T3
; Z_HEIGHT: 13.6
G1 X1 Y2 Z13.6
; FEATURE: Outer wall
G1 X3 E.1
G1 E-.2
G1 X4
M82
G92 E5
G1 X6 E5.2
; FEATURE: Custom
G1 X30 E6
'''
        paths,moves,_=surface_paths(gcode)
        self.assertEqual(moves,2)
        self.assertEqual(len(paths),2)
        np.testing.assert_allclose(paths[0]['xy'],[[1,2],[3,2]])
        np.testing.assert_allclose(paths[1]['xy'],[[4,2],[6,2]])
        self.assertEqual(paths[0]['tool'],4)


if __name__=='__main__':
    unittest.main()
