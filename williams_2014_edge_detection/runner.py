import os
from .constants import IMAGE_DIR, FILENAMES, MASK_SIZES, N_MC, DISPLAY
from .processing import process_image
from .display import build_ks_binary_for_display, show_edge_on_black


def main():
    all_tables = {}
    total_files = len(FILENAMES)

    for file_idx, fname in enumerate(FILENAMES):
        path = os.path.join(IMAGE_DIR, fname)
        if not os.path.exists(path):
            print(f"File not found: {path}. Skipping.")
            continue

        print(f"\n[{file_idx+1}/{total_files}] Processing {fname}")
        df, im, gt = process_image(path, MASK_SIZES, n_mc=N_MC)

        pivot = df.pivot(index='test', columns='mask_size', values='pcm_mean').round(3)
        pivot_std = df.pivot(index='test', columns='mask_size', values='pcm_std').round(3)
        combined = pivot.copy().astype(str)
        for m in MASK_SIZES:
            combined[m] = pivot[m].astype(str) + " ± " + pivot_std[m].astype(str)
        combined = combined[[m for m in MASK_SIZES]]
        print(f"\nPCM mean ± std (g=1) for image: {fname}")
        print(combined)
        all_tables[fname] = df

        print("  Generating display image...")
        display_mask = 11 if 11 in MASK_SIZES else MASK_SIZES[0]
        bw_thin = build_ks_binary_for_display(path, display_mask)
        print(f"Displaying detected edges for: {fname}")
        if DISPLAY:
            show_edge_on_black(bw_thin, fname)

    return all_tables


if __name__ == "__main__":
    print("Running statistical edge detection (based on modified Experiment 2 in Williams et al., 2014).")
    print(f"Processing {len(FILENAMES)} images with {N_MC} Monte Carlo iterations each.")
    print(f"Mask sizes: {MASK_SIZES}")
    print(f"Tests: DoB, T, F, L, U, KS, v2")
    print("=" * 60)

    tables = main()

    print("\n" + "=" * 60)
    print("All processing complete!")


# TODO check if that shi works as intended after refactor