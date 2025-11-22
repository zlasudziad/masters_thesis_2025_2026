import os
from PIL import Image
from .constants import IMAGE_DIR, FILENAMES, MASK_SIZES, N_MC, DISPLAY, PROJECT_ROOT
from .processing import process_image
from .display import build_ks_binary_for_display, show_edge_on_black
from .saving import make_attempt_dir, save_table


def _fmt_mean_std(mean, std):
    try:
        return f"{mean:.3f} ± {std:.3f}"
    except Exception:
        return f"{mean} ± {std}"


def main():
    all_tables = {}
    total_files = len(FILENAMES)

    # create attempt directory under project root
    attempt_dir, attempt_num = make_attempt_dir(prefix="attempt")
    print(f"Outputs will be saved under: {attempt_dir} (attempt {attempt_num})")

    for file_idx, fname in enumerate(FILENAMES):
        path = os.path.join(IMAGE_DIR, fname)
        if not os.path.exists(path):
            print(f"File not found: {path}. Skipping.")
            continue

        print(f"\n[{file_idx+1}/{total_files}] Processing {fname}")
        # pass attempt_dir and attempt_num so processing can save per-MC images and binaries
        df, im, gt = process_image(path, MASK_SIZES, n_mc=N_MC, out_dir=attempt_dir, attempt_num=attempt_num)

        pivot = df.pivot(index='test', columns='mask_size', values='pcm_mean').round(3)
        pivot_std = df.pivot(index='test', columns='mask_size', values='pcm_std').round(3)
        combined = pivot.copy().astype(str)
        # format combined cells with mean ± std
        for m in MASK_SIZES:
            try:
                combined[m] = [ _fmt_mean_std(pivot.loc[idx, m], pivot_std.loc[idx, m]) for idx in combined.index ]
            except Exception:
                # leave as-is if formatting fails
                pass
        combined = combined[[m for m in MASK_SIZES]]
        print(f"\nPCM mean ± std (g=1) for image: {fname}")
        print(combined)
        all_tables[fname] = df

        print("  Generating display image...")
        display_mask = 11 if 11 in MASK_SIZES else MASK_SIZES[0]
        bw_thin = build_ks_binary_for_display(path, display_mask)
        print(f"Displaying detected edges for: {fname}")
        canvas = show_edge_on_black(bw_thin, fname)
        # if DISPLAY is False or matplotlib not available, save fallback image
        if canvas is not None:
            out_dir = os.path.join(attempt_dir, 'json_outputs')
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f"detected_{os.path.basename(fname)}")
            try:
                Image.fromarray(canvas).save(out_path)
            except Exception as e:
                print("Failed to save display canvas:", e)

        # save table for this image
        try:
            tables_out_dir = os.path.join(attempt_dir, 'tables')
            saved_table = save_table(df, tables_out_dir, 'results', path, attempt_num, N_MC)
            print(f"Saved results table to: {saved_table}")
        except Exception as e:
            print("Failed to save results table:", e)

        if DISPLAY:
            try:
                show_edge_on_black(bw_thin, fname)
            except Exception:
                pass

    # also save aggregated tables
    try:
        all_df = None
        import pandas as pd
        all_df = pd.concat(all_tables.values(), ignore_index=True)
        agg_saved = save_table(all_df, os.path.join(attempt_dir, 'tables'), 'all_results', 'all_images', attempt_num, N_MC)
        print(f"Aggregated table saved to: {agg_saved}")
    except Exception as e:
        print("Failed to save aggregated table:", e)

    print("\n" + "=" * 60)
    print("All processing complete!")

    return all_tables


if __name__ == '__main__':
    main()
