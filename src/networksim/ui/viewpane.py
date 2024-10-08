import tkinter as tk

from networksim.hardware.cable import Cable
from networksim.hardware.device import Device
from networksim.hardware.interface import AlreadyConnectedException
from networksim.hardware.interface import Interface
from networksim.simulation import Simulation
from networksim.ui.addwindow import AddWindow
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

        self.drag_start_x = None
        self.drag_start_y = None

        self.bind("<ButtonPress-1>", self.start_drag)
        self.bind("<B1-Motion>", self.drag)
        self.bind("<ButtonPress-3>", self.right_click)
        self.last_event = 0

    def remove_menu(self, event):
        if self.menu is not None:
            self.menu.destroy()

    @dedupe_click
    def right_click(self, event):
        self.remove_menu(event)

    @dedupe_click
    def start_drag(self, event):
        self.remove_menu(event)

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

    def start_connect(self, device: DeviceShape):
        print(f"Starting connect: {device.device.name}")
        self.connect_start = device.device

    def select_connect_end(self, device: DeviceShape):
        print(f"Connecting to: {device.device.name}")
        AddWindow(
            self,
            cls=Cable,
            callback=self.get_end_connect_handler(
                self.connect_start,
                device.device,
            ),
            ignore_list=["a", "b"],
        )

    def get_end_connect_handler(self, a: Device, b: Device):
        def handler(cable: Cable):
            try:
                cable.a = [x for x in a.ifaces if not x.connected][0]
                cable.b = [x for x in b.ifaces if not x.connected][0]
                self.sim.add_cable(cable)
            except IndexError:
                cable.a = None
                cable.b = None
                ErrorWindow(
                    self,
                    text=f"One or more devices already connected:\n* {a.name}\n* {b.name}",
                )
            finally:
                self.connect_start = None

        return handler

    def delete_device(self, device: DeviceShape):
        print(f"DELETING: {device.device.name}")
        self.sim.delete_device(device.device, remove_cables=True)
        device.delete()
        self.devices.remove(device)
