"""A1 orientation and conservative motion settings for the tilted copper parts."""
import numpy as np
import trimesh

TRAVEL = {'travel_speed': ['150'], 'travel_acceleration': ['1000'],
          'initial_layer_travel_acceleration': ['500'],
          'default_acceleration': ['1000'], 'outer_wall_acceleration': ['500'],
          'inner_wall_acceleration': ['1000'], 'sparse_infill_acceleration': ['1000'],
          'top_surface_acceleration': ['500'], 'initial_layer_acceleration': ['500'],
          'gap_infill_speed': ['150'], 'inner_wall_speed': ['150'],
          'internal_solid_infill_speed': ['150'], 'sparse_infill_speed': ['150'],
          'outer_wall_speed': ['150'], 'top_surface_speed': ['150']}
TRAVEL.update({k:['1000','1000'] for k in ['machine_max_acceleration_x','machine_max_acceleration_y',
              'machine_max_acceleration_extruding','machine_max_acceleration_travel']})
TRAVEL.update({k:['150','150'] for k in ['machine_max_speed_x','machine_max_speed_y']})
COPPER = {'default_acceleration': '1000', 'outer_wall_acceleration': '500',
          'inner_wall_acceleration': '1000', 'sparse_infill_acceleration': '1000',
          'top_surface_acceleration': '500', 'initial_layer_acceleration': '500',
          'brim_type': 'outer_only', 'brim_width': '6', 'brim_object_gap': '0.1',
          'support_speed': '60', 'support_interface_speed': '40',
          'tree_support_branch_diameter': '3', 'tree_support_wall_count': '2'}
BAND_CENTERS = [(50,50),(110,50),(50,160),(110,160),(185,160)]
TEST_CENTERS = [(60,110),(128,110),(196,110)]


def rot(degrees,axis=(0,0,1)):
    return trimesh.transformations.rotation_matrix(np.deg2rad(degrees),axis)


def choose(mesh):
    """Face contains Y, leans across X, and stays 55 degrees above the bed.

    Optimize roll within that face for the lowest height that fits. Reserve
    9 mm each side in Y for brim/supports; verify actual sliced paths later.
    No scaling or new joints. Sampling is 0.25 degrees, not a safety proof.
    """
    pts=mesh.convex_hull.vertices; choices=[]
    for angle in np.arange(0,360,.25):
        t=rot(90)@rot(55,(1,0,0))@rot(float(angle))
        placed=pts@t[:3,:3].T;size=np.ptp(placed,axis=0)
        if size[0]<=230 and size[1]<=238 and size[2]<=246:
            choices.append((float(size[2]),float(angle),size,t))
    if not choices:raise ValueError('Part cannot fit with its face aligned to Y at 55 degrees.')
    height,angle,size,t=min(choices,key=lambda c:(c[0],c[1]))
    return center(mesh,t,(128,128)),size.tolist(),angle


def center(mesh,t,xy):
    t=t.copy();t[:3,3]=0;pts=mesh.vertices@t[:3,:3].T
    t[:2,3]=np.array(xy)-(pts.min(axis=0)+pts.max(axis=0))[:2]/2
    t[2,3]=-pts[:,2].min()
    return t
