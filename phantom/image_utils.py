import numpy as np
from PIL import Image, ImageTk


def load_png_as_rgba(path: str, target_width: int = None) -> Image:
    img = Image.open(path).convert("RGBA")
    if target_width is not None and img.width != target_width:
        scale = target_width / img.width
        new_h = int(img.height * scale)
        img = img.resize((target_width, new_h), Image.NEAREST)
    return img


def make_background_layer(shape_k: float, scale_theta: float, canvas_w: int, canvas_h: int) -> Image:
    noise = np.random.gamma(shape_k, scale_theta, size=(canvas_h, canvas_w))
    noise = (noise - noise.min()) / max(noise.max() - noise.min(), 1e-9)
    noise = (noise * 255).astype(np.uint8)
    bg_arr = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)
    for i in range(3):
        bg_arr[:, :, i] = noise
    bg_arr[:, :, 3] = 255
    return Image.fromarray(bg_arr, mode="RGBA")


def fill_layer_with_gamma(layer, shape_k: float, scale_theta: float):
    """Fill a LayerItem (or PIL image) with gamma noise preserving alpha.

    If `layer` has attributes `original_image`, `pil_image`, `tk_image` it will update them in-place.
    Otherwise it returns a PIL Image with the filled data.
    """
    # accept either a LayerItem-like or a PIL Image
    try:
        arr = np.array(layer.original_image)
    except Exception:
        # assume layer is a PIL.Image
        arr = np.array(layer)

    alpha = arr[:, :, 3]
    mask = alpha > 0
    if not mask.any():
        # nothing to do
        if hasattr(layer, "pil_image"):
            return
        else:
            return Image.fromarray(arr, mode="RGBA")

    h, w = mask.shape
    noise = np.random.gamma(shape_k, scale_theta, size=(h, w))
    noise = (noise - noise.min()) / max(noise.max() - noise.min(), 1e-9)
    noise = (noise * 255).astype(np.uint8)

    out = np.zeros_like(arr)
    for i in range(3):
        out[:, :, i] = noise
    out[:, :, 3] = alpha
    out_img = Image.fromarray(out, mode="RGBA")

    if hasattr(layer, "pil_image"):
        layer.pil_image = out_img
        # update tk image lazily; GUI should recreate ImageTk.PhotoImage when needed
        layer.tk_image = ImageTk.PhotoImage(layer.pil_image)
        return

    return out_img


def gamma_noise_image(shape_k: float, scale_theta: float, width: int, height: int) -> Image:
    noise = np.random.gamma(shape_k, scale_theta, size=(height, width))
    noise = (noise - noise.min()) / max(noise.max() - noise.min(), 1e-9)
    noise = (noise * 255).astype(np.uint8)
    img_arr = np.stack([noise] * 3 + [np.full((height, width), 255, dtype=np.uint8)], axis=-1)
    return Image.fromarray(img_arr, mode="RGBA")


def create_rotated_image(upper_params, lower_params, angle: float, expanded_size: int, img_size: int):
    from PIL import Image
    img = Image.new("RGBA", (expanded_size, expanded_size))
    upper = gamma_noise_image(upper_params["shape"], upper_params["scale"], expanded_size, expanded_size // 2)
    img.paste(upper, (0, 0))
    lower = gamma_noise_image(lower_params["shape"], lower_params["scale"], expanded_size, expanded_size // 2)
    img.paste(lower, (0, expanded_size // 2))
    rotated = img.rotate(angle, resample=Image.BICUBIC, expand=False)
    left = (expanded_size - img_size) // 2
    upper_crop = (expanded_size - img_size) // 2
    return rotated.crop((left, upper_crop, left + img_size, upper_crop + img_size))

