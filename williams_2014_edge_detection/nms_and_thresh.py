import numpy as np
from skimage.filters import apply_hysteresis_threshold


def non_max_suppression(response, angle_map):
    """
    Simple non-maximal suppression along orientation vector (angle_map in degrees).
    Compares pixel to neighbors at +/-1 along the angle and keeps if local maximum.
    """
    H, W = response.shape
    out = np.zeros_like(response)

    for i in range(H):
        for j in range(W):
            ang = angle_map[i, j]
            if np.isnan(ang):
                continue
            theta = np.deg2rad(ang)
            dx = np.cos(theta)
            dy = np.sin(theta)
            p1 = (i + int(round(dy)), j + int(round(dx)))
            p2 = (i - int(round(dy)), j - int(round(dx)))
            val = response[i, j]
            v1 = response[p1] if 0 <= p1[0] < H and 0 <= p1[1] < W else -np.inf
            v2 = response[p2] if 0 <= p2[0] < H and 0 <= p2[1] < W else -np.inf
            if val >= v1 and val >= v2:
                out[i, j] = val
    return out


def hysteresis_and_binary(nms_img, high, low):
    """Apply hysteresis thresholding and return binary image (uint8)."""
    high = np.clip(high, 0, 255)
    low = np.clip(low, 0, 255)
    bw = apply_hysteresis_threshold(nms_img.astype(float), low, high)
    return bw.astype(np.uint8)

