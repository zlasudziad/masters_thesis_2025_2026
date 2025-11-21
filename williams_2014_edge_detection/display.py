import numpy as np
from skimage.morphology import thin
from .masks import make_dual_region_mask
from .stats_tests import compute_tests_region
from .nms_and_thresh import non_max_suppression, hysteresis_and_binary
from .constants import HIGHS, LOW_RATIO
from .io_utils import load_gray


def show_edge_on_black(edge_binary, filename=None):
    """Create a black canvas and draw white edges; minimal display helper kept here.
    This function intentionally does not import matplotlib at module import time to keep
    import lightweight; callers can import matplotlib and show if desired.
    """
    try:
        import matplotlib.pyplot as plt
    except Exception:
        plt = None

    canvas = np.zeros(edge_binary.shape, dtype=np.uint8)
    canvas[edge_binary > 0] = 255
    if plt is not None:
        plt.figure(figsize=(6, 6))
        if filename:
            plt.title(filename)
        plt.imshow(canvas, cmap='gray', vmin=0, vmax=255)
        plt.axis('off')
        plt.show()
    else:
        # fallback: return canvas
        return canvas


def build_ks_binary_for_display(image_path, display_mask, high_threshold=None, angles=None):
    """Build a KS-based binary edge image for display from a single pass.
    Optional `angles` list can be provided to restrict orientations (e.g., [90] for top/bottom split).
    Returns binary thin edge image (uint8).
    """
    im = load_gray(image_path)
    H, W = im.shape
    responses = np.zeros_like(im, dtype=float)
    angle_map = np.full(im.shape, np.nan)
    half = display_mask // 2
    # determine angles: use provided list, otherwise default choice based on mask size
    if angles is None:
        if display_mask == 5:
            angles = np.linspace(0, 180, 12, endpoint=False)
        else:
            angles = np.linspace(0, 180, 20, endpoint=False)
    # ensure angles is iterable
    angles = list(angles)

    for i in range(half, H - half):
        for j in range(half, W - half):
            patch = im[i - half:i + half + 1, j - half:j + half + 1]
            best_ks = -np.inf
            best_ang = None
            for ang in angles:
                A_mask, B_mask = make_dual_region_mask(display_mask, ang)
                a_vals = patch[A_mask]
                b_vals = patch[B_mask]
                if a_vals.size == 0 or b_vals.size == 0:
                    continue
                ks = compute_tests_region(a_vals, b_vals)["KS"]
                if ks > best_ks:
                    best_ks = ks
                    best_ang = ang
            responses[i, j] = best_ks if best_ks > -np.inf else 0.0
            angle_map[i, j] = best_ang if best_ang is not None else np.nan
    if responses.max() - responses.min() < 1e-9:
        norm_disp = np.zeros_like(responses, dtype=np.uint8)
    else:
        norm_disp = ((responses - responses.min()) / (responses.max() - responses.min()) * 255).astype(np.uint8)
    nms_disp = non_max_suppression(norm_disp, angle_map)
    # choose representative threshold
    ThH = np.median(HIGHS) if high_threshold is None else high_threshold
    ThL = LOW_RATIO * ThH
    bw = hysteresis_and_binary(nms_disp, ThH, ThL)
    bw_thin = thin(bw > 0).astype(np.uint8)
    return bw_thin
