import os
from williams_2014_edge_detection.processing import process_image
from williams_2014_edge_detection.display import build_ks_binary_for_display, show_edge_on_black
from williams_2014_edge_detection.constants import IMAGE_DIR


def run_demo():
    img = os.path.join(IMAGE_DIR, '0_background_NFL.png')
    if not os.path.exists(img):
        print('Demo image not found:', img)
        return
    print('Running demo on', img)
    # run process_image with one Monte Carlo iteration and mask size [19]
    df, im, gt = process_image(img, [19], n_mc=1)
    print(df)
    # horizontal split (top/bottom) by using angle 90 degrees
    # TODO check if that's correct or did I fuuuck it up
    bw = build_ks_binary_for_display(img, 19, angles=[90])
    # show (or return) the result
    show_edge_on_black(bw, os.path.basename(img))


if __name__ == '__main__':
    run_demo()





