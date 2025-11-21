import numpy as np


def make_dual_region_mask(size, angle_deg):
    """Create bool masks (A_mask, B_mask) for a square mask size x size.
    Split by a line through the center at angle angle_deg.
    A_mask is one side, B_mask the other, central pixel not included
    in either A or B.
    """
    s = size
    cx = (s - 1) / 2.0
    cy = (s - 1) / 2.0
    ys, xs = np.mgrid[0:s, 0:s].astype(float)
    # coordinates relative to center
    xr = xs - cx
    yr = ys - cy
    # unit normal for the split line
    theta = np.deg2rad(angle_deg)
    # split by sign of dot product with normal vector
    nx = np.cos(theta)
    ny = np.sin(theta)
    dot = xr * nx + yr * ny
    # exclude the center pixel from A and B
    center_mask = (np.abs(xs - cx) < 0.5) & (np.abs(ys - cy) < 0.5)
    A = (dot > 0) & (~center_mask)
    B = (dot < 0) & (~center_mask)
    return A, B

