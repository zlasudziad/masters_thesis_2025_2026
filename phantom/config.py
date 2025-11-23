import json
import sys
from typing import Dict, Any
from pathlib import Path
import os

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
    """Load gamma parameters.

    Search order:
    1. Path specified by environment variable GAMMA_PARAMETERS_PATH (if set)
    2. Project-root/json_outputs/<path>
    3. Project-root/<path>

    Project root is resolved relative to this module location (two levels up).
    Raises FileNotFoundError if not found. No defaults are returned by this function.
    """
    # 1) env var override
    env_override = os.environ.get("GAMMA_PARAMETERS_PATH")
    if env_override:
        p_env = Path(env_override)
        if p_env.exists():
            with open(p_env, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f"GAMMA_PARAMETERS_PATH is set but file not found: {p_env}")

    # Resolve project root from this file location to avoid CWD issues
    project_root = Path(__file__).resolve().parents[1]
    p_json_outputs = project_root / "json_outputs" / path
    p_root = project_root / path

    for p in (p_json_outputs, p_root):
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)

    raise FileNotFoundError(f"Could not find {path} in json_outputs/ or project root (checked {p_json_outputs} and {p_root})")
