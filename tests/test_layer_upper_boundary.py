import numpy as np
from PIL import Image
from phantom.layer import LayerItem
from phantom.editor import LayerEditorApp
import tkinter as tk


def test_get_layer_upper_boundary_small():
    # create a small image 10x6 with an alpha column at x=2 and x=5
    w, h = 10, 6
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    # make two columns with non-transparent pixels at rows 2 and 3
    arr[2:, 2, 3] = 255
    arr[3:, 5, 3] = 255
    img = Image.fromarray(arr, mode="RGBA")
    li = LayerItem("test", img, y=4)

    root = tk.Tk()
    app = LayerEditorApp(root, [li], canvas_w=15, canvas_h=20)
    out = app.get_layer_upper_boundary(li)
    # column 2 should have top at y=4+2=6, column 5 at y=4+3=7
    assert out[2] == 6
    assert out[5] == 7
    # others should be None
    assert all(out[i] is None for i in range(15) if i not in (2, 5))
    root.destroy()

