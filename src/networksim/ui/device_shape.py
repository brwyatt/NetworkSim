import inspect
import tkinter as tk
from dataclasses import dataclass
from dataclasses import make_dataclass
from typing import Optional
from typing import TYPE_CHECKING

import pkg_resources
from networksim.hardware.device import Device
from networksim.hardware.interface import Interface
from networksim.ipaddr import IPAddr
from networksim.ipaddr import IPNetwork
from networksim.ui.addwindow import AddWindow

if TYPE_CHECKING:
    from networksim.ui.viewpane import ViewPane


@dataclass
class ip_bind:
    addr: IPAddr
    network: IPNetwork


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

        self.update_handlers = []

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

    def send_updates(self):
        for handler in self.update_handlers:
            handler()

    def add_update_handler(self, handler):
        if handler not in self.update_handlers:
            self.update_handlers.append(handler)

    def del_update_handler(self, handler):
        if handler in self.update_handlers:
            self.update_handlers.remove(handler)

    def get_midpoint(self):
        x1, y1, x2, y2 = self.canvas.coords(self.rect)
        return (x1 + ((x2 - x1) / 2)), (y1 + ((y2 - y1) / 2))

    def delete(self):
        for shape in self.shapes:
            self.canvas.delete(shape)

    def get_add_application_handler(self, entry_point):
        def handler():
            self.device.add_application(entry_point.load(), entry_point.name)

        return handler

    def create_add_application_menu(self, master, handler_generator):
        app_menu = tk.Menu(master, tearoff=False)

        for entry_point in pkg_resources.iter_entry_points(
            "networksim_applications",
        ):
            if entry_point.name in self.device.applications:
                continue
            app_menu.add_command(
                label=entry_point.name,
                command=handler_generator(entry_point),
            )

        return app_menu

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

    def get_add_bind_handler(self, iface: Interface):
        def handler():
            AddWindow(
                master=self.canvas.winfo_toplevel(),
                cls=ip_bind,
                callback=lambda bind: self.device.ip.bind(
                    addr=bind.addr,
                    network=bind.network,
                    iface=iface,
                ),
            )

        return handler

    def get_delete_bind_handler(self, addr: IPAddr, iface: Interface):
        def handler():
            self.device.ip.unbind(addr=addr, iface=iface)

        return handler

    def get_garp_handler(self, addr: IPAddr, iface: Interface):
        def handler():
            self.device.ip.send_garp(addr=addr, iface=iface)

        return handler

    def create_ip_binds_menu(self, master):
        binds_menu = tk.Menu(master, tearoff=False)

        iface_num = -1
        for iface in self.device.ifaces:
            iface_num += 1
            if not iface.connected:
                continue
            iface_menu = tk.Menu(binds_menu, tearoff=False)
            for bind in self.device.ip.bound_ips.get_binds(iface=iface):
                bind_menu = tk.Menu(iface_menu, tearoff=False)
                bind_menu.add_command(
                    label="Remove Bind",
                    command=self.get_delete_bind_handler(
                        addr=bind.addr,
                        iface=iface,
                    ),
                )
                bind_menu.add_command(
                    label="Send Gratuitous ARP",
                    command=self.get_garp_handler(addr=bind.addr, iface=iface),
                )
                iface_menu.add_cascade(
                    label=f"{bind.addr}/{bind.network.match_bits}",
                    menu=bind_menu,
                )
            iface_menu.add_command(
                label="Add Bind",
                command=self.get_add_bind_handler(iface),
            )
            binds_menu.add_cascade(
                label=f"{iface_num} - ({str(iface.hwid)})",
                menu=iface_menu,
            )

        return binds_menu

    def get_start_application_handler(self, name, application):
        sig = inspect.signature(application)
        fields = []
        for field in sig.parameters.values():
            if field.name in ["device", "args", "kwargs"]:
                continue
            if field.default == inspect.Parameter.empty:
                fields.append((field.name, field.annotation))
            else:
                fields.append((field.name, field.annotation, field.default))
        datacls = make_dataclass(name, fields)

        def callback(data):
            self.device.start_application(name, **data.__dict__)

        def handler():
            if len(fields) == 0:
                callback(datacls())
            else:
                AddWindow(
                    master=self.canvas.winfo_toplevel(),
                    cls=datacls,
                    callback=callback,
                )

        return handler

    def create_start_application_menu(self, master):
        app_menu = tk.Menu(master, tearoff=False)

        for name, application in self.device.applications.items():
            app_menu.add_command(
                label=name,
                command=self.get_start_application_handler(name, application),
            )

        return app_menu

    def raise_shapes(self):
        for shape in self.shapes:
            self.canvas.tag_raise(shape)

    def create_menu(self, event):
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

        add_app_menu = self.create_add_application_menu(
            menu,
            self.get_add_application_handler,
        )
        menu.add_cascade(label="Add Application", menu=add_app_menu)

        if hasattr(self.device, "ip"):
            ip_binds_menu = self.create_ip_binds_menu(menu)
            menu.add_cascade(label="IP Binds", menu=ip_binds_menu)

        if len(self.device.applications) > 0:
            start_app_menu = self.create_start_application_menu(menu)
            menu.add_cascade(label="Start Application", menu=start_app_menu)

        menu.post(event.x_root, event.y_root)
        self.canvas.menu = menu

        return menu

    def right_click(self, event):
        self.canvas.last_event = event.serial
        self.canvas.remove_menu(event)

        self.raise_shapes()

        self.create_menu(event)

    def get_start_connect_handler(self, iface):
        def handler():
            self.canvas.start_connect(self, iface)

        return handler

    def get_end_connect_handler(self, iface):
        def handler():
            self.canvas.select_connect_end(self, iface)

        return handler

    def left_click(self, event):
        self.raise_shapes()

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

    def drag(self, event):
        if self.canvas.connect_start is not None:
            return

        self.canvas.last_event = event.serial
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y

        for shape in self.shapes:
            self.canvas.move(shape, dx, dy)

        self.send_updates()

        self.drag_start_x = event.x
        self.drag_start_y = event.y
