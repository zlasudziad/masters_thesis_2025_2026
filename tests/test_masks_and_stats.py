import numpy as np
from williams_2014_edge_detection.masks import make_dual_region_mask
from williams_2014_edge_detection.stats_tests import compute_tests_region


def test_make_dual_region_mask_basic():
    A, B = make_dual_region_mask(5, 0)
    assert A.shape == (5, 5) and B.shape == (5, 5)
    # center should be excluded
    cx = 2
    assert not A[cx, cx] and not B[cx, cx]
    # both regions should be non-empty and disjoint
    assert A.sum() > 0 and B.sum() > 0
    assert not (A & B).any()


def test_compute_tests_region_on_simple_arrays():
    a = np.array([10, 10, 10, 10], dtype=float)
    b = np.array([20, 20, 20, 20], dtype=float)
    res = compute_tests_region(a, b)
    assert 'DoB' in res and res['DoB'] == 10.0
    assert res['KS'] >= 0
    assert res['v2'] >= 0
