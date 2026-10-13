"""Slice original triangles without Manifold's coplanar face regrouping.

On dense OpenSCAD seams Manifold.slice can introduce a triangular notch that
is absent from the original STL triangle-plane intersections. Color masks and
boundary audits must use those original intersections as their reference.
"""
import numpy as np
import manifold3d
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from shapely import make_valid

def mesh_slice(mesh,z):
    path=mesh.section(plane_origin=[0,0,z],plane_normal=[0,0,1])
    result=Polygon()
    if path is None:return result
    for loop in path.discrete:
        assert np.linalg.norm(loop[0]-loop[-1])<1e-6,'Open section contour'
        p=Polygon(loop[:,:2])
        if not p.is_valid:
            # A plane extremely close to a mesh vertex can produce a
            # point-touch or numerical self-crossing in a closed path.
            fixed=make_valid(p)
            assert abs(fixed.area-p.area)<1e-7,('Invalid triangle-plane contour',z,abs(fixed.area-p.area))
            p=fixed
        result=result.symmetric_difference(p)
    assert result.is_valid
    return result

def mesh_cross_section(mesh,z):
    shape=mesh_slice(mesh,z);rings=[]
    for p in ([shape] if shape.geom_type=='Polygon' else shape.geoms):
        if p.is_empty:continue
        p=orient(p,1)
        rings.append(np.asarray(p.exterior.coords)[:-1])
        rings.extend(np.asarray(h.coords)[:-1] for h in p.interiors)
    return manifold3d.CrossSection(rings)
