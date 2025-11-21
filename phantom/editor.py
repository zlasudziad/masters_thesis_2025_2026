import tkinter as tk
from tkinter import filedialog, messagebox
import json
from PIL import Image, ImageTk
import numpy as np
from typing import List
from pathlib import Path

from .layer import LayerItem
from .image_utils import load_png_as_rgba, make_background_layer, fill_layer_with_gamma
from .config import CANVAS_W, CANVAS_H, PNG_FILES, LAYER_NAMES, load_gamma_parameters

# TODO make sure this works after refactor because if not i'm going to do a m

class LayerEditorApp:
    def __init__(self, root: tk.Tk, layers: List[LayerItem], canvas_w: int, canvas_h: int):
        self.root = root
        self.root.title("Drag and drop layers editor")
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h
        self.layers = layers
        self.drag_data = {"item": None, "y0": 0, "mouse_y0": 0}

        self.canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="white")
        self.canvas.pack()

        self.draw_all()

        self.canvas.tag_bind("layer", "<ButtonPress-1>", self.on_press)
        self.canvas.tag_bind("layer", "<B1-Motion>", self.on_motion)
        self.canvas.tag_bind("layer", "<ButtonRelease-1>", self.on_release)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def draw_all(self):
        self.canvas.delete("all")
        for li in self.layers:
            li.tk_image = ImageTk.PhotoImage(li.pil_image)
            li.canvas_id = self.canvas.create_image(0, li.y, anchor="nw", image=li.tk_image, tags=("layer", li.name))
        for li in self.layers:
            self.canvas.tag_raise(li.canvas_id)

    def on_press(self, event):
        clicked = self.canvas.find_withtag("current")
        if not clicked:
            return
        cid = clicked[0]
        li = None
        for item in self.layers[::-1]:
            if item.canvas_id == cid:
                li = item
                break
        if li is None or not li.draggable:
            return
        self.drag_data["item"] = li
        self.drag_data["y0"] = li.y
        self.drag_data["mouse_y0"] = event.y

    def on_motion(self, event):
        li = self.drag_data["item"]
        if not li:
            return
        dy = event.y - self.drag_data["mouse_y0"]
        new_y = self.drag_data["y0"] + dy
        h = li.pil_image.height
        new_y = max(-h + 1, min(self.canvas_h - 1, new_y))
        li.y = int(new_y)
        self.canvas.coords(li.canvas_id, 0, li.y)

    def on_release(self, event):
        self.drag_data = {"item": None, "y0": 0, "mouse_y0": 0}

    def get_layer_upper_boundary(self, li: LayerItem):
        arr = np.array(li.pil_image)
        alpha = arr[:, :, 3]
        h, w = alpha.shape

        out = [None] * self.canvas_w
        cols_to_process = min(w, self.canvas_w)

        for x in range(cols_to_process):
            col = alpha[:, x]
            idx = np.where(col > 0)[0]
            if idx.size == 0:
                out[x] = None
            else:
                top_in_img = int(idx.min())
                out[x] = int(li.y + top_in_img)

        return out

    def save_all(self):
        out = []
        for li in self.layers:
            if li.name == "background" or not li.draggable:
                continue
            out.append({
                "name": li.name,
                "y": int(li.y),
                "upper_boundary_px": self.get_layer_upper_boundary(li),
            })
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        with open(path, "w") as f:
            json.dump(out, f, indent=2)
        messagebox.showinfo("Saved", f"Saved to {path}")

    def export_composite(self):
        comp = Image.new("RGBA", (self.canvas_w, self.canvas_h), (0, 0, 0, 0))
        for li in self.layers:
            comp.alpha_composite(li.pil_image, dest=(0, li.y))
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if not path:
            return
        comp.save(path)
        messagebox.showinfo("Exported", f"Saved to {path}")

    def fill_all_layers(self):
        try:
            gamma_by_name = load_gamma_parameters()
        except Exception:
            messagebox.showerror("Error", "Could not load gamma parameters")
            return

        for li in self.layers:
            if li.name == "background":
                continue
            params = gamma_by_name[li.name]
            fill_layer_with_gamma(li, params["shape"], params["scale"])
            self.canvas.itemconfig(li.canvas_id, image=li.tk_image)

    def on_close(self):
        try:
            gamma_by_name = load_gamma_parameters()
        except Exception:
            gamma_by_name = {}

        try:
            for li in self.layers:
                if li.name == "background":
                    continue
                params = gamma_by_name.get(li.name)
                if params:
                    fill_layer_with_gamma(li, params["shape"], params["scale"])
                    self.canvas.itemconfig(li.canvas_id, image=li.tk_image)

            out = []
            for li in self.layers:
                if li.name == "background" or not li.draggable:
                    continue
                out.append({
                    "name": li.name,
                    "y": int(li.y),
                    "upper_boundary_px": self.get_layer_upper_boundary(li),
                })
            out_dir = Path("json_outputs")
            out_dir.mkdir(parents=True, exist_ok=True)
            positions_path = out_dir / "layer_positions.json"
            with open(positions_path, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2)

            comp = Image.new("RGBA", (self.canvas_w, self.canvas_h), (0, 0, 0, 0))
            for li in self.layers:
                comp.alpha_composite(li.pil_image, dest=(0, li.y))
            comp.save("phantom.png")

            print(f"Auto-saved positions to {positions_path} and composite.png")
        except Exception as e:
            print("Error saving on close:", e)
        finally:
            self.root.destroy()


def main(run: bool = True, canvas_w: int = CANVAS_W, canvas_h: int = CANVAS_H, png_files=None, layer_names=None):
    if png_files is None:
        png_files = PNG_FILES
    if layer_names is None:
        layer_names = LAYER_NAMES

    root = tk.Tk()

    if len(png_files) != len(layer_names) - 1:
        print("Mismatch: PNG_FILES must correspond to all layers except background")
        return None

    try:
        gamma_by_name = load_gamma_parameters()
    except FileNotFoundError:
        print("gamma_parameters.json not found")
        return None

    layers = []
    bg_params = gamma_by_name["background"]
    bg_layer = LayerItem("background", make_background_layer(bg_params["shape"], bg_params["scale"], canvas_w, canvas_h), init_y=0, draggable=False)
    layers.append(bg_layer)

    for png_path, layer_name in zip(png_files, layer_names[1:]):
        params = gamma_by_name[layer_name]
        img_rgba = load_png_as_rgba(png_path, target_width=canvas_w)
        layers.append(LayerItem(layer_name, img_rgba, init_y=0))

    app = LayerEditorApp(root, layers, canvas_w, canvas_h)
    if run:
        root.mainloop()
    return app
