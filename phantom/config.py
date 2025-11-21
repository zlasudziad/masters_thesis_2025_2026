import json
import sys
from typing import Dict, Any

CANVAS_W = 1536
CANVAS_H = 900

PNG_FILES = [
    "pngs/NFL.png",
    "pngs/GCL.png",
    "pngs/IPL.png",
    "pngs/INL.png",
    "pngs/OPL.png",
    "pngs/ONL.png",
    "pngs/ELM.png",
    "pngs/OPR.png",
    "pngs/RPE.png",
]

LAYER_NAMES = [
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


def load_gamma_parameters(path: str = "gamma_parameters.json") -> Dict[str, Any]:
    with open(path, "r") as f:
        return json.load(f)

