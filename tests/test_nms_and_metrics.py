import numpy as np
from williams_2014_edge_detection.nms_and_thresh import non_max_suppression, hysteresis_and_binary
from williams_2014_edge_detection.metrics import compute_pcm_binary


def test_non_max_suppression_basic():
    resp = np.zeros((5, 5), dtype=float)
    resp[2, 2] = 10
    angle_map = np.full((5, 5), np.nan)
    angle_map[2, 2] = 0.0
    out = non_max_suppression(resp, angle_map)
    assert out[2, 2] == 10


def test_hysteresis_and_binary_and_pcm():
    # create a simple ramp image where center is high
    img = np.zeros((5, 5), dtype=np.uint8)
    img[2, 2] = 255
    bw = hysteresis_and_binary(img, 200, 100)
    assert bw.dtype == np.uint8
    assert bw[2, 2] == 1 or bw[2, 2] == 255

    # PCM: perfect match
    det = np.zeros((5, 5), dtype=np.uint8)
    gt = np.zeros((5, 5), dtype=np.uint8)
    det[2, 2] = 1
    gt[2, 2] = 1
    pcm = compute_pcm_binary(det, gt, g=1)
    assert pcm == 100.0

