"""Regression checks for smooth joins, circular samples and a real ripple."""
import copy,unittest
import numpy as np
from rebuild_clean_cad import sample_ring,clean_shapes
from review_clean_edges import arc_error
from rebuild_clean_partitions import partition_shapes
from validate_print_project import CAD
from validate_print_project import STLS
from mesh_sections import mesh_slice,mesh_cross_section
from review_curve_artifacts import shape_from_section
from shapely.geometry import Point
import trimesh

class CleanOutlineTests(unittest.TestCase):
    def circle(self):
        return [dict(type='circle',start=[10,0],end=[0,10],center=[0,0],radius=10,sign=1,sweep_degrees=90),
                dict(type='circle',start=[0,10],end=[-10,0],center=[0,0],radius=10,sign=1,sweep_degrees=90),
                dict(type='circle',start=[-10,0],end=[0,-10],center=[0,0],radius=10,sign=1,sweep_degrees=90),
                dict(type='circle',start=[0,-10],end=[10,0],center=[0,0],radius=10,sign=1,sweep_degrees=90)]

    def test_circle_chords_have_bounded_error_and_no_waves(self):
        p,proof=sample_ring(self.circle())
        np.testing.assert_allclose(np.linalg.norm(p,axis=1),10,atol=1e-12)
        mids=(p+np.roll(p,-1,axis=0))/2
        self.assertLess(float((10-np.linalg.norm(mids,axis=1)).max()),.002)
        self.assertLess(proof['max_tangent_discontinuity_degrees'],1e-10)

    def test_disconnected_or_nontangent_arc_is_rejected(self):
        p=self.circle();p[1]['center']=[.1,0]
        with self.assertRaises(AssertionError):sample_ring(p)

    def test_gradual_ripple_is_detected_without_sharp_vertices(self):
        theta=np.linspace(.5,1,501)
        radius=10+.12*np.sin(np.linspace(0,4*np.pi,len(theta)))
        p=radius[:,None]*np.column_stack([np.cos(theta),np.sin(theta)])
        result=arc_error(p,self.circle()[0],np.array([10.]))
        self.assertGreater(result[0],.11)
        clean=10*np.column_stack([np.cos(theta),np.sin(theta)])
        self.assertLess(arc_error(clean,self.circle()[0],np.array([10.]))[0],1e-12)

    def test_every_saved_loop_and_shared_fabric_boundary(self):
        knot,fabric,_,checks=clean_shapes()
        self.assertEqual(len(checks),26)
        self.assertEqual(sum(c['primitives'] for c in checks),320)
        self.assertLess(knot.intersection(fabric).area,1e-7)
        self.assertTrue(knot.is_valid and fabric.is_valid)

    def test_new_partition_covers_clean_artwork_without_overlap(self):
        masks,domains,proof=partition_shapes(CAD.read_text())
        self.assertEqual((len(masks),len(domains)),(20,31))
        self.assertLess(proof['partition_coverage_error_mm2'],1e-7)
        self.assertLess(proof['maximum_mask_overlap_inside_frame_mm2'],1e-7)

    def test_oblique_weave_seam_does_not_acquire_false_triangle(self):
        mesh=trimesh.load_mesh(STLS/'F6.stl')
        # Strictly inside the native thread where Manifold's 3D face
        # regrouping previously produced a false triangular notch.
        p=Point(50.248,105.92)
        self.assertTrue(mesh_slice(mesh,9.3).contains(p))
        self.assertTrue(shape_from_section(mesh_cross_section(mesh,9.3)).contains(p))

if __name__=='__main__':unittest.main()
