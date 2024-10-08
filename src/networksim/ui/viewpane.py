import tkinter as tk

from networksim.hardware.device import Device
from networksim.hardware.interface import AlreadyConnectedException
from networksim.simulation import Simulation
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

    def end_connect(self, device: DeviceShape):
        print(f"Connecting to: {device.device.name}")
        try:
            self.sim.connect_devices(self.connect_start, device.device)
        except AlreadyConnectedException:
            ErrorWindow(
                self,
                text=f"One or more devices already connected:\n* {self.connect_start.name}\n* {device.device.name}",
            )
        finally:
            self.connect_start = None

    def delete_device(self, device: DeviceShape):
        print(f"DELETING: {device.device.name}")
        self.sim.delete_device(device.device, remove_cables=True)
        device.delete()
        self.devices.remove(device)
