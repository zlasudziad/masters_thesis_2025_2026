import os
import re
from typing import Tuple
from skimage import io
import numpy as np
from .constants import PROJECT_ROOT


def make_attempt_dir(prefix: str = "attempt") -> Tuple[str, int]:
    """Create and return a new attempt directory under PROJECT_ROOT.

    Scans PROJECT_ROOT for existing directories named like `prefix_###` and
    creates the next sequential directory (e.g. attempt_001, attempt_002...).

    Returns (attempt_dir_path, attempt_number).
    """
    pattern = re.compile(rf'^{re.escape(prefix)}_(\d+)$')
    maxn = 0
    for name in os.listdir(PROJECT_ROOT):
        path = os.path.join(PROJECT_ROOT, name)
        if os.path.isdir(path):
            m = pattern.match(name)
            if m:
                try:
                    n = int(m.group(1))
                    if n > maxn:
                        maxn = n
                except ValueError:
                    pass
    nextn = maxn + 1
    attempt_name = f"{prefix}_{nextn:03d}"
    attempt_dir = os.path.join(PROJECT_ROOT, attempt_name)
    os.makedirs(attempt_dir, exist_ok=True)
    return attempt_dir, nextn


def _safe_basename(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def format_image_filename(what: str, source_path: str, attempt_num: int, total_mc: int,
                          mc_idx: int, mask_size: int, ext: str = ".png") -> str:
    """Return a filename with the required metadata encoded.

    Example:
      bw_DoB_src-0_background_NFL_attempt-001_mcTotal-5_mc-3_mask-19.png
    """
    src = _safe_basename(source_path)
    what_clean = what.replace(' ', '_')
    return f"{what_clean}_src-{src}_attempt-{attempt_num:03d}_mcTotal-{total_mc}_mc-{mc_idx}_mask-{mask_size}{ext}"


def save_binary_image(arr: np.ndarray, out_dir: str, what: str, source_path: str,
                      attempt_num: int, total_mc: int, mc_idx: int, mask_size: int) -> str:
    """Save a binary (0/1 or boolean) image as uint8 PNG and return path."""
    os.makedirs(out_dir, exist_ok=True)
    # normalize to 0..255 uint8
    if arr.dtype != np.uint8:
        try:
            arr_to_save = (arr.astype(bool).astype(np.uint8) * 255)
        except Exception:
            arr_to_save = (arr > 0).astype(np.uint8) * 255
    else:
        arr_to_save = (arr > 0).astype(np.uint8) * 255

    fname = format_image_filename(what, source_path, attempt_num, total_mc, mc_idx, mask_size)
    out_path = os.path.join(out_dir, fname)
    io.imsave(out_path, arr_to_save)
    return out_path


def format_table_filename(base: str, source_path: str, attempt_num: int, total_mc: int, ext: str = ".csv") -> str:
    src = _safe_basename(source_path)
    return f"{base}_src-{src}_attempt-{attempt_num:03d}_mcTotal-{total_mc}{ext}"


def save_table(df, out_dir: str, base: str, source_path: str, attempt_num: int, total_mc: int) -> str:
    os.makedirs(out_dir, exist_ok=True)
    fname = format_table_filename(base, source_path, attempt_num, total_mc)
    out_path = os.path.join(out_dir, fname)
    # let pandas handle writing
    try:
        df.to_csv(out_path, index=False)
    except Exception:
        # fallback to json
        df.to_json(out_path + ".json")
        out_path = out_path + ".json"
    return out_path

