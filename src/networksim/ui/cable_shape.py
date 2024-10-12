import tkinter as tk
from typing import TYPE_CHECKING

from networksim.hardware.cable import Cable
from networksim.ui.device_shape import DeviceShape

if TYPE_CHECKING:
    from networksim.ui.viewpane import ViewPane


class CableShape:
    def __init__(
        self,
        cable: Cable,
        canvas: "ViewPane",
        device_a: DeviceShape,
        device_b: DeviceShape,
    ):
        self.cable = cable
        self.canvas = canvas
        self.a = device_a
        self.b = device_b

        self.line = self.canvas.create_line(
            *self.a.get_midpoint(),
            *self.b.get_midpoint(),
            width=5,
        )

        self.a.add_update_handler(self.update_location)
        self.b.add_update_handler(self.update_location)

        canvas.tag_bind(self.line, "<ButtonPress-1>", self.left_click)
        canvas.tag_bind(self.line, "<ButtonPress-3>", self.right_click)

        self.raise_shapes()

    def update_location(self):
        self.canvas.coords(
            self.line,
            *self.a.get_midpoint(),
            *self.b.get_midpoint(),
        )

    def delete(self):
        self.a.del_update_handler(self.update_location)
        self.b.del_update_handler(self.update_location)
        self.canvas.delete(self.line)

    def raise_shapes(self):
        self.canvas.tag_raise(self.line)
        self.a.raise_shapes()
        self.b.raise_shapes()

    def create_menu(self, event):
        menu = tk.Menu(self.canvas, tearoff=0)
        menu.add_command(
            label="Delete",
            command=lambda: self.canvas.delete_cable(self),
        )

        menu.post(event.x_root, event.y_root)
        self.canvas.menu = menu

        return menu

    def left_click(self, event):
        self.canvas.last_event = event.serial
        self.canvas.remove_menu(event)

        self.raise_shapes()

    def right_click(self, event):
        self.canvas.last_event = event.serial
        self.canvas.remove_menu(event)

        self.raise_shapes()

        self.create_menu(event)
