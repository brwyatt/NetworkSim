import tkinter as tk

from networksim.hardware.device import Device
from networksim.simulation import Simulation
from networksim.ui.device_shape import DeviceShape


class ViewPane(tk.Canvas):
    def __init__(self, master=None, *args, sim: Simulation):
        super().__init__(master=master, width=800, height=600, bg="white")

        self.sim = sim

        self.devices = []
        self.menu = None

        self.bind("<ButtonPress-1>", self.start_drag)
        self.bind("<B1-Motion>", self.drag)
        self.bind("<ButtonPress-3>", self.right_click)
        self.last_event = 0

    def remove_menu(self, event):
        if self.menu is not None:
            self.menu.destroy()

    def right_click(self, event):
        if event.serial == self.last_event:
            # Dedupe clicks passing through from shapes
            return
        self.last_event = event.serial

        self.remove_menu(event)

    def start_drag(self, event):
        if event.serial == self.last_event:
            # Dedupe clicks passing through from shapes
            return
        self.last_event = event.serial

        self.remove_menu(event)

        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def drag(self, event):
        if event.serial == self.last_event:
            # Dedupe clicks passing through from shapes
            return
        self.last_event = event.serial

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

    def delete_device(self, device: DeviceShape):
        print(f"DELETING: {device.device.name}")
        self.sim.delete_device(device.device)
        device.delete()
        self.devices.remove(device)
