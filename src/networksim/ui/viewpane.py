import tkinter as tk
from typing import Tuple

from networksim.hardware.cable import Cable
from networksim.hardware.device import Device
from networksim.hardware.interface import AlreadyConnectedException
from networksim.hardware.interface import Interface
from networksim.simulation import Simulation
from networksim.ui.addwindow import AddWindow
from networksim.ui.cable_draw_shape import CableDrawShape
from networksim.ui.cable_shape import CableShape
from networksim.ui.device_shape import DeviceShape
from networksim.ui.errorwindow import ErrorWindow


def dedupe_click(func):
    def handler(self, event):
        if event.serial == self.last_event:
            # Dedupe clicks passing through from shapes
            return
        self.last_event = event.serial

        return func(self, event)

    return handler


class ViewPane(tk.Canvas):
    def __init__(self, master=None, *args, sim: Simulation):
        super().__init__(master=master, width=800, height=600, bg="white")

        self.sim = sim

        self.devices = []
        self.menu = None
        self.connect_start = None
        self.draw_cable = None
        self.cables = []

        self.drag_start_x = None
        self.drag_start_y = None

        self.bind("<ButtonPress-1>", self.left_click)
        self.bind("<B1-Motion>", self.drag)
        self.bind("<ButtonPress-3>", self.right_click)
        self.last_event = 0

    def remove_menu(self, event):
        if self.menu is not None:
            self.menu.destroy()
        self.menu = None

    @dedupe_click
    def right_click(self, event):
        self.remove_menu(event)
        self.cancel_connect()

    @dedupe_click
    def left_click(self, event):
        self.remove_menu(event)
        self.cancel_connect()
        self.start_drag(event)

    def start_drag(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    @dedupe_click
    def drag(self, event):
        if self.drag_start_x is None or self.drag_start_y is None:
            return
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        self.move(tk.ALL, dx, dy)
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def add_device(self, device: Device):
        print(f"ADDING: {device.name}")
        self.sim.add_device(device)
        shape = DeviceShape(
            device=device,
            canvas=self,
            x=(self.winfo_width() / 2) - 25,
            y=(self.winfo_height() / 2) - 25,
            width=50,
            height=50,
        )
        self.devices.append(shape)

    def start_connect(self, device: DeviceShape, iface: Interface):
        print(f"Starting connect: {device.device.name} - {iface.hwid}")
        self.connect_start = (device, iface)
        self.draw_cable = CableDrawShape(self, device)

    def cancel_connect(self):
        if self.draw_cable is not None:
            self.draw_cable.delete()
            self.draw_cable = None

    def select_connect_end(self, device: DeviceShape, iface: Interface):
        print(f"Connecting to: {device.device.name} - {iface.hwid}")
        AddWindow(
            self,
            cls=Cable,
            callback=self.get_end_connect_handler(
                self.connect_start,
                (device, iface),
            ),
            ignore_list=["a", "b"],
        )

    def get_end_connect_handler(
        self,
        a: Tuple[DeviceShape, Interface],
        b: Tuple[DeviceShape, Interface],
    ):
        def handler(cable: Cable):
            try:
                cable.a = a[1]
                cable.b = b[1]
                self.sim.add_cable(cable)
            except AlreadyConnectedException:
                cable.a = None
                cable.b = None
                ErrorWindow(
                    self,
                    text=f"One or more ports already connected:\n* {a[0].device.name} - {a[1].hwid}\n* {b[0].device.name} - {b[1].hwid}",
                )
                return
            finally:
                self.connect_start = None

            self.cancel_connect()

            shape = CableShape(
                cable=cable,
                canvas=self,
                device_a=a[0],
                device_b=b[0],
            )
            self.cables.append(shape)

        return handler

    def step(self):
        for cable in self.cables:
            cable.draw_packets()

    def delete_cable(self, cable: Cable):
        try:
            self.sim.delete_cable(cable.cable)
        except ValueError:
            pass
        cable.delete()
        self.cables.remove(cable)

    def delete_device(self, device: DeviceShape):
        print(f"DELETING: {device.device.name}")
        self.sim.delete_device(device.device, remove_cables=True)
        device.delete()
        self.devices.remove(device)
        for cable in list(self.cables):
            if device == cable.a or device == cable.b:
                self.delete_cable(cable)
