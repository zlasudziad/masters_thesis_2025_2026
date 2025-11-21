from williams_2014_edge_detection.io_utils import load_gray
import os


def test_load_gray_exists_and_uint8():
    path = os.path.join(os.getcwd(), 'gamma_layers_horizontal_squares', '0_background_NFL.png')
    assert os.path.exists(path), f"Test image not found: {path}"
    im = load_gray(path)
    assert im.dtype == 'uint8'
    assert im.ndim == 2
    # simple sanity: not all zeros
    assert im.sum() > 0

