"""Build a phantom composite image from a JSON file with layer names and positions.

Usage:
  python scripts/build_phantom_from_json.py --json json_outputs/layer_positions.json --out phantom_from_json.png

Defaults:
  json: json_outputs/layer_positions.json
  out : phantom_from_json.png

The script uses `phantom.config` for canvas size, PNG file list and gamma parameters and
`phantom.image_utils` to load and fill layers with gamma noise. It composites layers in the
order defined by `LAYER_NAMES` so background should be first.
"""
from __future__ import annotations
import json
import argparse
import sys
from pathlib import Path
from PIL import Image
from typing import List, Dict, Any

# ensure project root is importable so `from phantom ...` works when running this script
proj_root = Path(__file__).resolve().parents[1]
if str(proj_root) not in sys.path:
    sys.path.insert(0, str(proj_root))

from phantom.config import CANVAS_W, CANVAS_H, PNG_FILES, LAYER_NAMES, load_gamma_parameters
from phantom.image_utils import load_png_as_rgba, make_background_layer, fill_layer_with_gamma


def load_positions(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_phantom_from_positions(positions: List[Dict[str, Any]], canvas_w: int, canvas_h: int,
                                 png_files: List[str], layer_names: List[str], gamma_params: Dict[str, Any]) -> Image.Image:
    """Return a composite PIL Image (RGBA) created from the positions list.

    positions is a list of dicts with at least keys: 'name', 'y'.
    gamma_params maps layer name -> {'shape':..., 'scale':...}
    png_files corresponds (in order) to layer_names[1:] (i.e. all layers except background)
    """
    # map names to position entries
    pos_by_name = {p['name']: p for p in positions if 'name' in p}

    # Create blank canvas
    comp = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

    # background first
    bg_params = gamma_params.get('background') if gamma_params else None
    if bg_params:
        bg = make_background_layer(bg_params.get('shape', 1.0), bg_params.get('scale', 1.0), canvas_w, canvas_h)
        comp.alpha_composite(bg, dest=(0, 0))
    else:
        # leave transparent background if no params
        pass

    # For each non-background layer in order, load the PNG, place it at y, fill with gamma if possible and composite
    for png_rel, layer_name in zip(png_files, layer_names[1:]):
        try:
            img = load_png_as_rgba(png_rel, target_width=canvas_w)
        except Exception as e:
            print(f"Warning: could not load PNG for layer '{layer_name}' from '{png_rel}': {e}")
            # create a transparent placeholder
            img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

        entry = pos_by_name.get(layer_name)
        y = int(entry.get('y', 0)) if entry is not None and 'y' in entry else 0

        # fill with gamma noise if parameters available
        params = gamma_params.get(layer_name) if gamma_params else None
        if params:
            try:
                img_filled = fill_layer_with_gamma(img, params.get('shape', 1.0), params.get('scale', 1.0))
                # fill_layer_with_gamma returns an Image when given a PIL.Image
                if img_filled is not None:
                    img = img_filled
            except Exception as e:
                print(f"Warning: could not fill layer '{layer_name}' with gamma: {e}")

        # clip y to reasonable range to avoid errors
        if y < -img.height + 1:
            y = -img.height + 1
        if y > canvas_h - 1:
            y = canvas_h - 1

        try:
            comp.alpha_composite(img, dest=(0, y))
        except Exception as e:
            print(f"Warning: failed to composite layer '{layer_name}' at y={y}: {e}")

    return comp


def main():
    parser = argparse.ArgumentParser(description="Build phantom from layer positions JSON")
    parser.add_argument("--json", type=str, default="json_outputs/layer_positions.json", help="Path to positions JSON")
    parser.add_argument("--gamma", type=str, default="json_outputs/gamma_parameters.json", help="Path to gamma parameters JSON")
    parser.add_argument("--out", type=str, default="phantom_from_json.png", help="Output composite PNG path")
    parser.add_argument("--canvas-w", type=int, default=CANVAS_W)
    parser.add_argument("--canvas-h", type=int, default=CANVAS_H)
    args = parser.parse_args()

    json_path = Path(args.json)
    if not json_path.exists():
        print(f"Positions JSON not found: {json_path}")
        return

    try:
        positions = load_positions(json_path)
    except Exception as e:
        print(f"Failed to load positions JSON: {e}")
        return

    gamma_path = Path(args.gamma)
    if not gamma_path.exists():
        print(f"Gamma parameters JSON not found: {gamma_path}")
        gamma = {}
    else:
        try:
            gamma = load_gamma_parameters(str(gamma_path))
        except Exception as e:
            print(f"Failed to load gamma parameters from {gamma_path}: {e}")
            gamma = {}

    comp = build_phantom_from_positions(positions, args.canvas_w, args.canvas_h, PNG_FILES, LAYER_NAMES, gamma)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    comp.save(out_path)
    print(f"Saved composite to {out_path}")


if __name__ == '__main__':
    main()
