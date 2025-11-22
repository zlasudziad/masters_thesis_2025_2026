import os
import time
import numpy as np
import pandas as pd
from skimage.morphology import thin

from .io_utils import load_gray
from .masks import make_dual_region_mask
from .stats_tests import compute_tests_region
from .nms_and_thresh import non_max_suppression, hysteresis_and_binary
from .metrics import compute_pcm_binary
from .constants import N_MC, G_PCM, HIGHS, LOW_RATIO

# import saving helper but keep optional to avoid hard dependency in tests
try:
    from .saving import save_binary_image
except Exception:
    save_binary_image = None


def process_image(image_path, mask_sizes, n_mc=N_MC, out_dir: str = None, attempt_num: int = None):
    """Process image and optionally save per-MC, per-mask best thin binaries when out_dir and attempt_num are provided.

    Returns (df, im, gt) as before.
    """
    save_outputs = out_dir is not None and attempt_num is not None and save_binary_image is not None

    print(f"  Loading image: {os.path.basename(image_path)}")
    im = load_gray(image_path)
    H, W = im.shape
    # create ground-truth: horizontal single-pixel edge at middle row
    gt = np.zeros_like(im, dtype=np.uint8)
    mid_row = H // 2
    gt[mid_row, :] = 1

    tests = ["DoB", "T", "F", "L", "U", "KS", "v2"]
    results = {t: {m: [] for m in mask_sizes} for t in tests}

    for mc in range(n_mc):
        print(f"    Monte Carlo iteration {mc+1}/{n_mc}")
        if n_mc > 1:
            noise = np.random.normal(loc=0.0, scale=0.5, size=im.shape)
            im_mc = np.clip(im.astype(float) + noise, 0, 255).astype(np.uint8)
        else:
            im_mc = im.copy()

        for msize in mask_sizes:
            print(f"      Processing mask size {msize}x{msize}")
            start_time = time.time()
            if msize == 5:
                angles = np.linspace(0, 180, 12, endpoint=False)
            else:
                angles = np.linspace(0, 180, 20, endpoint=False)

            resp_maps = {t: np.zeros_like(im_mc, dtype=float) for t in tests}
            angle_map = np.full(im_mc.shape, np.nan)
            half = msize // 2

            total_pixels = (H - 2*half) * (W - 2*half)
            pixels_processed = 0
            # EWMA state for per-pixel timing estimator
            ewma_per_pixel = None
            print(f"        Processing {total_pixels} pixels...")

            for i in range(half, H - half):
                for j in range(half, W - half):
                    best_vals = {t: -np.inf for t in tests}
                    best_angle = None
                    patch = im_mc[i - half:i + half + 1, j - half:j + half + 1]
                    for ang in angles:
                        A_mask, B_mask = make_dual_region_mask(msize, ang)
                        A_vals = patch[A_mask]
                        B_vals = patch[B_mask]
                        stats_dict = compute_tests_region(A_vals, B_vals)
                        for t in tests:
                            v = stats_dict[t]
                            if v > best_vals[t]:
                                best_vals[t] = v
                        avg_resp = np.mean(list(stats_dict.values()))
                        if best_angle is None or avg_resp > best_angle[0]:
                            best_angle = (avg_resp, ang)
                    for t in tests:
                        resp_maps[t][i, j] = best_vals[t]
                    angle_map[i, j] = best_angle[1] if best_angle is not None else np.nan

                    pixels_processed += 1
                    # report progress periodically; use a smaller interval for responsiveness
                    if pixels_processed % 100 == 0 or pixels_processed == total_pixels:
                        now = time.time()
                        elapsed = now - start_time
                        # compute average time per processed pixel and use it to estimate remaining time
                        if pixels_processed > 0 and elapsed > 0:
                            avg_per_pixel = elapsed / float(pixels_processed)
                            # use instantaneous average per-pixel as estimator (keeps code simple and deterministic)
                            ewma_per_pixel = avg_per_pixel
                            remaining = total_pixels - pixels_processed
                            eta = avg_per_pixel * remaining
                        else:
                            eta = 0.0

                        # format ETA in H:M:S
                        hrs = int(eta // 3600)
                        mins = int((eta % 3600) // 60)
                        secs = int(eta % 60)
                        if hrs > 0:
                            eta_str = f"{hrs}h{mins:02d}m{secs:02d}s"
                        elif mins > 0:
                            eta_str = f"{mins}m{secs:02d}s"
                        else:
                            eta_str = f"{secs}s"

                        print(
                            f"          MC {mc + 1}/{n_mc}, "
                            f"Image {os.path.basename(image_path)}, "
                            f"Mask {msize} | "
                            f"{pixels_processed}/{total_pixels} px "
                            f"({(pixels_processed / total_pixels) * 100:.1f}% ) "
                            f"ETA {eta_str}"
                        )

            print("100% - done")

            print(f"        Post-processing for {len(tests)} tests...")
            for t_idx, t in enumerate(tests):
                print(f"          Test {t_idx+1}/{len(tests)}: {t}")
                rmap = resp_maps[t]
                mn, mx = np.nanmin(rmap), np.nanmax(rmap)
                if mx - mn < 1e-9:
                    norm = np.zeros_like(rmap, dtype=np.uint8)
                else:
                    norm = ((rmap - mn) / (mx - mn) * 255.0).astype(np.uint8)
                nms = non_max_suppression(norm, angle_map)
                pcm_scores = []
                bw_thin_list = []
                for th_idx, ThH in enumerate(HIGHS):
                    ThL = LOW_RATIO * ThH
                    bw = hysteresis_and_binary(nms, ThH, ThL)
                    bw_thin = thin(bw > 0).astype(np.uint8)
                    bw_thin_list.append(bw_thin)
                    pcm_val = compute_pcm_binary(bw_thin, gt, g=G_PCM)
                    pcm_scores.append(pcm_val)
                best_idx = int(np.nanargmax(pcm_scores)) if len(pcm_scores) > 0 else 0
                best_pcm = float(np.max(pcm_scores)) if len(pcm_scores) > 0 else np.nan
                results[t][msize].append(best_pcm)

                # optionally save the best thin binary for this test/mask/mc
                if save_outputs:
                    try:
                        best_bw = bw_thin_list[best_idx]
                        images_out = os.path.join(out_dir, 'images')
                        # save all thin binaries and mark the best one with a _best suffix
                        for th_idx, bw_thin in enumerate(bw_thin_list):
                            is_best = (th_idx == best_idx)
                            what = f"bw_{t}_th{th_idx+1}"
                            if is_best:
                                what = what + "_best"
                            saved = save_binary_image(bw_thin, images_out, what, image_path, attempt_num, n_mc, mc+1, msize)
                            # log saved path for the best one to avoid too much console spam
                            if is_best:
                                print(f"            Saved best bw for test={t}, mask={msize}, mc={mc+1} -> {saved}")
                    except Exception as e:
                        print("            Failed to save binary image:", e)

    print("    Computing statistics...")
    summary_rows = []
    for t in tests:
        for m in mask_sizes:
            arr = np.array(results[t][m], dtype=float)
            mean_pcm = np.mean(arr) if arr.size > 0 else np.nan
            std_pcm = np.std(arr, ddof=1) if arr.size > 1 else 0.0
            summary_rows.append({
                "test": t,
                "mask_size": m,
                "pcm_mean": mean_pcm,
                "pcm_std": std_pcm
            })
    df = pd.DataFrame(summary_rows)
    return df, im, gt
