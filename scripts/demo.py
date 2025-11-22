import os
from williams_2014_edge_detection.processing import process_image
from williams_2014_edge_detection.display import build_ks_binary_for_display, show_edge_on_black
from williams_2014_edge_detection.constants import IMAGE_DIR
from williams_2014_edge_detection.saving import make_attempt_dir, save_table


def run_demo():
    img = os.path.join(IMAGE_DIR, '0_background_NFL.png')
    if not os.path.exists(img):
        print('Demo image not found:', img)
        return
    print('Running demo on', img)

    # create attempt dir
    attempt_dir, attempt_num = make_attempt_dir(prefix="demo")
    print(f"Demo outputs will be saved under: {attempt_dir} (attempt {attempt_num})")

    # run process_image with one Monte Carlo iteration and mask size [19]
    df, im, gt = process_image(img, [19], n_mc=1, out_dir=attempt_dir, attempt_num=attempt_num)
    print(df)

    # save table
    try:
        saved = save_table(df, os.path.join(attempt_dir, 'tables'), 'demo_results', img, attempt_num, 1)
        print('Saved demo table to', saved)
    except Exception as e:
        print('Failed to save demo table:', e)

    # horizontal split (top/bottom) by using angle 90 degrees
    bw = build_ks_binary_for_display(img, 19, angles=[90])
    # show (or return) the result and save fallback
    canvas = show_edge_on_black(bw, os.path.basename(img))
    if canvas is not None:
        out_dir = os.path.join(attempt_dir, 'images')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"demo_detected_{os.path.basename(img)}")
        try:
            from PIL import Image
            Image.fromarray(canvas).save(out_path)
            print('Saved demo image to', out_path)
        except Exception as e:
            print('Failed to save demo image:', e)


if __name__ == '__main__':
    run_demo()
