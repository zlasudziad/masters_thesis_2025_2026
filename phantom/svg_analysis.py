import math
import numpy as np
from svgpathtools import svg2paths
from typing import List, Tuple


def angle_of(v) -> float:
    return math.degrees(math.atan2(v.imag, v.real))


def angles_for_segment(seg, samples: int = 50) -> List[float]:
    ts = np.linspace(0, 1, samples)
    return [angle_of(seg.derivative(t)) for t in ts]


def load_svg_paths(path: str):
    return svg2paths(path)


def collect_cubic_angles(paths, samples: int = 50):
    all_angles = []
    for path in paths:
        for seg in path:
            if seg.__class__.__name__ == "CubicBezier":
                all_angles.extend(angles_for_segment(seg, samples=samples))
    # can we normalize having angles only in [-180, 180] range
    all_angles = [(a + 180) % 360 - 180 for a in all_angles]
    return all_angles


if __name__ == "__main__":
    paths, attrs = load_svg_paths("other_files/layer_paths.svg")
    angles = collect_cubic_angles(paths)
    print("Min angle:", min(angles))
    print("Max angle:", max(angles))











