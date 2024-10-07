import tkinter as tk
from typing import Optional

from networksim.hardware.device import Device


class DeviceShape:
    def __init__(
        self,
        device: Device,
        canvas: tk.Canvas,
        x: int,
        y: int,
        width: int = 50,
        height: int = 50,
        label: Optional[str] = None,
    ):
        self.device = device
        self.canvas = canvas
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        font_size = 10

        self.bgrect = canvas.create_rectangle(
            x,
            y,
            x + width,
            y + height + font_size + 2,
            width=0,
        )
        self.rect = canvas.create_rectangle(
            x,
            y,
            x + width,
            y + height,
            fill="blue",
        )
        self.text = canvas.create_text(
            x + (width / 2),
            y + height + (font_size / 2) + 2,
            font=("Helvetica", font_size, "bold"),
            text=label if label is not None else device.name,
        )

        self.shapes = (self.bgrect, self.rect, self.text)
        for shape in self.shapes:
            canvas.tag_bind(shape, "<ButtonPress-1>", self.on_start)
            canvas.tag_bind(shape, "<B1-Motion>", self.on_drag)
            canvas.tag_bind(shape, "<Button-3>", self.right_click)

    def delete(self):
        for shape in self.shapes:
            self.canvas.delete(shape)

    def right_click(self, event):
        self.canvas.remove_menu(event)

        menu = tk.Menu(self.canvas, tearoff=0)
        menu.add_command(
            label="Delete",
            command=lambda: self.canvas.delete_device(self),
        )
        menu.post(event.x_root, event.y_root)
        self.canvas.menu = menu

    def on_start(self, event):
        self.canvas.remove_menu(event)

        self.drag_start_x = event.x
        self.drag_start_y = event.y

        for shape in self.shapes:
            self.canvas.tag_raise(shape)

    def on_drag(self, event):
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y

        for shape in self.shapes:
            self.canvas.move(shape, dx, dy)

        self.drag_start_x = event.x
        self.drag_start_y = event.y
