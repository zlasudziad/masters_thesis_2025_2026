from skimage import io, color, util
import numpy as np


def load_gray(path):
    """Load image as 8-bit grayscale (0..255).
    Keeps behavior from original module: handles RGB/RGBA and already grayscale images.
    """
    im = io.imread(path)

    # if image is RGBA (4 channels), drop alpha
    if im.ndim == 3 and im.shape[2] == 4:
        im = im[:, :, :3]

    if im.ndim == 3:
        im = color.rgb2gray(im)
        im = (im * 255).astype(np.uint8)
    else:
        if im.dtype != np.uint8:
            im = util.img_as_ubyte(im)

    return im

