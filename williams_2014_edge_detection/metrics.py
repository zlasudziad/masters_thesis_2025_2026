import numpy as np


def compute_pcm_binary(det_mask, gt_mask, g=1):
    """
    Greedy PCM match count with radius g. Returns percentage 0..100.
    """
    det_coords = np.column_stack(np.nonzero(det_mask))
    gt_coords = np.column_stack(np.nonzero(gt_mask))
    na = len(det_coords)
    nb = len(gt_coords)
    if na == 0 and nb == 0:
        return 100.0
    if na == 0 or nb == 0:
        return 0.0
    matched_gt = np.zeros(nb, dtype=bool)
    matches = 0
    for (r, c) in det_coords:
        dists = np.sqrt((gt_coords[:, 0] - r) ** 2 + (gt_coords[:, 1] - c) ** 2)
        valid_idxs = np.where((dists <= g) & (~matched_gt))[0]
        if valid_idxs.size > 0:
            chosen = valid_idxs[np.argmin(dists[valid_idxs])]
            matched_gt[chosen] = True
            matches += 1
    denom = max(na, nb)
    pcm = 100.0 * (matches / float(denom))
    return pcm

