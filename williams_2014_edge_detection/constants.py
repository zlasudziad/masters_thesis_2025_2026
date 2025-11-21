import os
import numpy as np

# Determine project root (parent directory of this package)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Directory with demo images (resolved relative to project root so scripts work from any CWD)
IMAGE_DIR = os.path.join(PROJECT_ROOT, "gamma_layers_horizontal_squares")

FILENAMES = [
    "0_background_NFL.png",
    "1_NFL_GCL.png",
    "2_GCL_IPL.png",
    "3_IPL_INL.png",
    "4_INL_OPL.png",
    "5_OPL_ONL.png",
    "6_ONL_ELM.png",
    "7_ELM_OPR.png",
    "8_OPR_RPE.png",
]
# mask sizes (use fuller set)
MASK_SIZES = [5, 11, 15, 19]
# Monte Carlo iterations (use value seen in later block)
N_MC = 5
# PCM localization tolerance (pixels)
G_PCM = 1
# high thresholds swept in paper
HIGHS = np.linspace(240, 20, 12)
# low threshold as fraction of high
LOW_RATIO = 0.4
# histogram bins for chi-square style v2
N_CHI_BINS = 16
# whether to display figures
DISPLAY = True
