import os
import json
from PIL import Image
from phantom.image_utils import gamma_noise_image, create_rotated_image

IMG_SIZE = 512
EXPANDED_SIZE = 1024

PAIRS = [
    ("background", "NFL"),
    ("NFL", "GCL"),
    ("GCL", "IPL"),
    ("IPL", "INL"),
    ("INL", "OPL"),
    ("OPL", "ONL"),
    ("ONL", "ELM"),
    ("ELM", "OPR"),
    ("OPR", "RPE"),
]

with open("gamma_parameters.json", "r") as f:
    GAMMA_PARAMS = json.load(f)

OUT_FOLDER = "gamma_layers_horizontal_squares"
os.makedirs(OUT_FOLDER, exist_ok=True)


def build_image(upper_params, lower_params):
    canvas = Image.new("RGBA", (IMG_SIZE, IMG_SIZE))
    upper = gamma_noise_image(upper_params["shape"], upper_params["scale"], IMG_SIZE, IMG_SIZE // 2)
    canvas.paste(upper, (0, 0))
    lower = gamma_noise_image(lower_params["shape"], lower_params["scale"], IMG_SIZE, IMG_SIZE // 2)
    canvas.paste(lower, (0, IMG_SIZE // 2))
    return canvas

for pair_idx, (first, second) in enumerate(PAIRS):
    p1 = GAMMA_PARAMS[first]
    p2 = GAMMA_PARAMS[second]
    img = build_image(p1, p2)
    img.save(f"{OUT_FOLDER}/{pair_idx}_{first}_{second}.png")

# angled
OUT_FOLDER = "gamma_layer_squares"
os.makedirs(OUT_FOLDER, exist_ok=True)
POSITIVE_ANGLES = [0]
NEGATIVE_ANGLES = [0]

def random_angle_deviation(angle, max_deviation=3):
    return 0

for pair_idx, (first, second) in enumerate(PAIRS):
    params1 = GAMMA_PARAMS[first]
    params2 = GAMMA_PARAMS[second]

    for angle_idx, angle in enumerate(POSITIVE_ANGLES):
        rand_angle = random_angle_deviation(angle)
        img = create_rotated_image(params1, params2, rand_angle, EXPANDED_SIZE, IMG_SIZE)
        img.save(f"{OUT_FOLDER}/{pair_idx}_{first}_{second}_pos_{angle_idx}.png")

    for angle_idx, angle in enumerate(NEGATIVE_ANGLES):
        rand_angle = random_angle_deviation(angle)
        img = create_rotated_image(params1, params2, rand_angle, EXPANDED_SIZE, IMG_SIZE)
        img.save(f"{OUT_FOLDER}/{pair_idx}_{first}_{second}_neg_{angle_idx}.png")

print("Generated square images")

