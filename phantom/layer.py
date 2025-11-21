from PIL import ImageTk
from dataclasses import dataclass
from typing import Optional
from PIL.Image import Image as PILImage


@dataclass
class LayerItem:
    name: str = None
    pil_image: PILImage = None
    y: int = 0
    draggable: bool = True
    original_image: PILImage = None
    tk_image: Optional[ImageTk.PhotoImage] = None
    canvas_id: Optional[int] = None

    def __init__(self, name: str, pil_image: PILImage, init_y: int = None, y: int = None, draggable: bool = True):
        self.name = name
        self.pil_image = pil_image
        self.original_image = pil_image.copy()
        self.tk_image = None
        # accept either y or init_y for compatibility
        if y is not None:
            chosen_y = y
        elif init_y is not None:
            chosen_y = init_y
        else:
            chosen_y = 0
        self.y = int(chosen_y)
        self.canvas_id = None
        self.draggable = bool(draggable)
