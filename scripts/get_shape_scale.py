import json
import logging
from pathlib import Path
from typing import Tuple, Dict, Optional

import cv2
import numpy as np

try:
    from PIL import Image
except Exception as e:
    raise ImportError("Pillow is required (pip install pillow).") from e

try:
    from scipy.stats import gamma
except Exception as e:
    raise ImportError("scipy is required (pip install scipy).") from e

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except Exception:
    tk = None

layer_names = [
    "background",
    "NFL",
    "GCL",
    "IPL",
    "INL",
    "OPL",
    "ONL",
    "ELM",
    "OPR",
    "RPE",
]


def load_image(path: Path) -> np.ndarray:
    """Load image as grayscale float64 array."""
    if not path.exists():
        raise FileNotFoundError(f"Input image not found: {path}")
    img = Image.open(path).convert("L")
    return np.asarray(img, dtype=np.float64)


def inverse_log_transform(I: np.ndarray) -> np.ndarray:
    """Apply inverse of the log-like transform."""
    # I expected in [0,255]
    I_clipped = np.clip(I, 0.0, 255.0)
    return (10.0 ** (I_clipped / 255.0) - 1.0) / 9.0


def estimate_gamma_params(region: np.ndarray) -> Tuple[float, float]:
    """Estimate gamma shape (k) and scale (theta) with floc=0.

    Raises:
        ValueError: when no valid positive samples exist.
        RuntimeError: when fitting fails.
    """
    data = region.flatten()
    data = data[np.isfinite(data) & (data > 0)]
    if data.size == 0:
        raise ValueError("No positive data points in region for gamma fit.")
    try:
        k, loc, theta = gamma.fit(data, floc=0)
    except Exception as e:
        raise RuntimeError(f"Gamma fit failed: {e}") from e
    return float(k), float(theta)


def select_rectangle(window_name: str, img: np.ndarray) -> Tuple[int, int, int, int]:
    """Interactive rectangle selection on a single-channel image.

    Returns (x, y, w, h) in image coordinates. Raises RuntimeError if the window
    is closed/cancelled by the user.
    """
    display_base = img.copy()
    if display_base.ndim == 2:
        display_bgr = cv2.cvtColor(display_base.astype(np.uint8), cv2.COLOR_GRAY2BGR)
    else:
        display_bgr = display_base.copy()

    img_h, img_w = display_bgr.shape[:2]
    rect = [0, 0, 0, 0]
    selecting = False
    scale = 1.0
    dx = dy = 0

    def clamp_img_coords(xi: int, yi: int) -> Tuple[int, int]:
        xi = max(0, min(img_w - 1, xi))
        yi = max(0, min(img_h - 1, yi))
        return xi, yi

    def win_to_img(wx: int, wy: int) -> Tuple[int, int]:
        xi = int((wx - dx) / scale)
        yi = int((wy - dy) / scale)
        return clamp_img_coords(xi, yi)

    def mouse(event, x, y, flags, param):
        nonlocal selecting, rect
        if event == cv2.EVENT_LBUTTONDOWN:
            selecting = True
            xi, yi = win_to_img(x, y)
            rect[0], rect[1] = xi, yi
            rect[2], rect[3] = xi, yi
        elif event == cv2.EVENT_MOUSEMOVE and selecting:
            xi, yi = win_to_img(x, y)
            rect[2], rect[3] = xi, yi
        elif event == cv2.EVENT_LBUTTONUP:
            selecting = False
            xi, yi = win_to_img(x, y)
            rect[2], rect[3] = xi, yi

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, mouse)

    try:
        while True:
            # detect if window was closed by user
            visible = cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE)
            if visible < 1:
                cv2.destroyWindow(window_name)
                raise RuntimeError("Selection window closed by user.")

            try:
                _, _, win_w, win_h = cv2.getWindowImageRect(window_name)
                if win_w <= 0 or win_h <= 0:
                    win_w, win_h = img_w, img_h
            except Exception:
                win_w, win_h = img_w, img_h

            scale_x = win_w / img_w
            scale_y = win_h / img_h
            scale = min(scale_x, scale_y) if min(scale_x, scale_y) > 0 else 1.0
            new_w = max(1, int(img_w * scale))
            new_h = max(1, int(img_h * scale))
            dx = (win_w - new_w) // 2
            dy = (win_h - new_h) // 2

            resized = cv2.resize(display_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
            canvas = np.zeros((win_h, win_w, 3), dtype=resized.dtype)
            canvas[dy : dy + new_h, dx : dx + new_w] = resized

            if rect[0] != rect[2] or rect[1] != rect[3]:
                sx = int(rect[0] * scale) + dx
                sy = int(rect[1] * scale) + dy
                ex = int(rect[2] * scale) + dx
                ey = int(rect[3] * scale) + dy
                cv2.rectangle(canvas, (sx, sy), (ex, ey), (0, 255, 0), 1)

            cv2.imshow(window_name, canvas)
            key = cv2.waitKey(20) & 0xFF
            if key in (ord("q"), 13):  # q or Enter
                break
    finally:
        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) >= 1:
            cv2.destroyWindow(window_name)

    x1, y1, x2, y2 = rect
    if x2 < x1:
        x1, x2 = x2, x1
    if y2 < y1:
        y1, y2 = y2, y1
    w = x2 - x1
    h = y2 - y1
    return x1, y1, w, h


def resolve_output_path(path: Path) -> Optional[Path]:
    """If the path exists, ask the user whether to overwrite, provide a new path, or cancel.

    Returns a Path to use for saving, or None if the user cancelled.
    """
    p = path
    while True:
        if not p.exists():
            return p
        resp = input(f"Output file `{p}` exists. Overwrite? [y/N]: ").strip().lower()
        if resp in ("y", "yes"):
            return p
        # treat default (empty) and 'n' as no
        new = input("Enter new output path or press Enter to cancel: ").strip()
        if new == "":
            return None
        p = Path(new)


def _pick_input_output_paths() -> Optional[tuple[Path, Path]]:
    """Return (input_path, output_path) chosen by the user.

    Use a tkinter file dialog when available; otherwise fall back to console prompts.
    Return None if the user cancels.
    """
    if tk is not None:
        root = tk.Tk()
        root.withdraw()
        filetypes = [("Image files", "*.png;*.bmp;*.jpg;*.jpeg;*.tif;*.tiff"), ("All files", "*")]
        input_path = filedialog.askopenfilename(title="Select input image", initialdir='.', filetypes=filetypes)
        root.destroy()
        if not input_path:
            print("No input selected. Aborting.")
            return None

        root = tk.Tk()
        root.withdraw()
        out_path = filedialog.asksaveasfilename(title="Save results as", defaultextension='.json', filetypes=[('JSON','*.json'),('All files','*.*')])
        root.destroy()
        if not out_path:
            print("No output selected. Aborting.")
            return None

        return Path(input_path), Path(out_path)

    # Console fallback
    inp = input("Path to input image: ").strip()
    if not inp:
        print("No input provided. Aborting.")
        return None
    out = input("Path to output JSON file (will be overwritten if exists): ").strip()
    if not out:
        print("No output provided. Aborting.")
        return None
    return Path(inp), Path(out)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    paths = _pick_input_output_paths()
    if paths is None:
        return

    input_path, output_path = paths

    try:
        I = load_image(input_path)
    except Exception as e:
        logging.error("Failed to load image: %s", e)
        return

    I_trans = inverse_log_transform(I)

    params: Dict[str, Dict[str, float]] = {}
    display = np.clip(I, 0, 255).astype(np.uint8)

    total = len(layer_names)
    for idx, name in enumerate(layer_names, start=1):
        title = f"Select region for {idx}: {name}"
        logging.info("Select region %d of %d: %s. Press Enter when done or q to accept.", idx, total, name)

        while True:
            try:
                x, y, w, h = select_rectangle(title, display)
            except RuntimeError as e:
                logging.warning("Selection cancelled: %s", e)
                return

            if w <= 0 or h <= 0:
                logging.warning("Empty selection — please click and drag to select a non-empty rectangle.")
                continue

            region = I_trans[y : y + h, x : x + w]
            try:
                shape, scale = estimate_gamma_params(region)
            except ValueError as e:
                logging.warning("Selection contains no valid positive data (%s). Please reselect.", e)
                continue
            except RuntimeError as e:
                logging.warning("Gamma fit failed: %s. Please reselect.", e)
                continue

            params[name] = {"shape": shape, "scale": scale}
            logging.debug("Stored params for %s: shape=%s scale=%s", name, shape, scale)
            break

    # if the output file exists, ask the user via the existing console helper (resolve_output_path)
    out_path = resolve_output_path(output_path)
    if out_path is None:
        logging.info("Saving aborted by user. No file written.")
        return

    try:
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(params, f, indent=4)
        logging.info("Saved results to %s", out_path)
    except Exception as e:
        logging.error("Failed to save output: %s", e)


if __name__ == "__main__":
    main()
