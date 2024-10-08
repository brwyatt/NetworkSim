import tkinter as tk
from typing import Optional
from typing import TYPE_CHECKING

from networksim.hardware.device import Device

if TYPE_CHECKING:
    from networksim.ui.viewpane import ViewPane


class DeviceShape:
    def __init__(
        self,
        device: Device,
        canvas: "ViewPane",
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
            canvas.tag_bind(shape, "<ButtonPress-1>", self.left_click)
            canvas.tag_bind(shape, "<B1-Motion>", self.drag)
            canvas.tag_bind(shape, "<ButtonPress-3>", self.right_click)

    def delete(self):
        for shape in self.shapes:
            self.canvas.delete(shape)

    def create_iface_menu(self, master, handler_generator):
        iface_menu = tk.Menu(master, tearoff=False)
        iface_num = -1
        for iface in self.device.ifaces:
            iface_num += 1
            if iface.connected:
                continue
            iface_menu.add_command(
                label=f"{iface_num} - ({str(iface.hwid)})",
                command=handler_generator(iface),
            )

        return iface_menu

    def right_click(self, event):
        self.canvas.last_event = event.serial
        self.canvas.remove_menu(event)

        menu = tk.Menu(self.canvas, tearoff=0)
        menu.add_command(
            label="Delete",
            command=lambda: self.canvas.delete_device(self),
        )
        iface_menu = self.create_iface_menu(
            menu,
            self.get_start_connect_handler,
        )
        menu.add_cascade(label="Connect", menu=iface_menu)
        menu.post(event.x_root, event.y_root)
        self.canvas.menu = menu

    def get_start_connect_handler(self, iface):
        def handler():
            self.canvas.start_connect(iface)

        return handler

    def get_end_connect_handler(self, iface):
        def handler():
            self.canvas.select_connect_end(iface)

        return handler

    def left_click(self, event):
        if (
            self.canvas.connect_start is not None
            and self.canvas.connect_start not in (self.device.ifaces)
        ):
            self.canvas.remove_menu(event)
            self.canvas.last_event = event.serial
            menu = self.create_iface_menu(
                self.canvas,
                self.get_end_connect_handler,
            )
            menu.post(event.x_root, event.y_root)
            self.canvas.menu = menu
        self.start_drag(event)

    def start_drag(self, event):
        self.canvas.last_event = event.serial

        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.canvas.drag_start_x = None
        self.canvas.drag_start_y = None

        for shape in self.shapes:
            self.canvas.tag_raise(shape)

    def drag(self, event):
        if self.canvas.connect_start is not None:
            return

        self.canvas.last_event = event.serial
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y

        for shape in self.shapes:
            self.canvas.move(shape, dx, dy)

        self.drag_start_x = event.x
        self.drag_start_y = event.y
