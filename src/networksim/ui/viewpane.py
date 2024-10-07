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

        self.bind("<ButtonPress-1>", self.remove_menu)
        self.bind("<ButtonPress-3>", self.remove_menu)
        self.last_event = 0

    def remove_menu(self, event):
        if event.serial == self.last_event:
            # Dedupe clicks passing through from shapes
            return
        if self.menu is not None:
            self.menu.destroy()
        self.last_event = event.serial

    def add_device(self, device: Device):
        print(f"ADDING: {device.name}")
        self.sim.add_device(device)
        shape = DeviceShape(
            device=device,
            canvas=self,
            x=(self.winfo_reqwidth() / 2) - 25,
            y=(self.winfo_reqheight() / 2) - 25,
            width=50,
            height=50,
        )
        self.devices.append(shape)

    def delete_device(self, device: DeviceShape):
        print(f"DELETING: {device.device.name}")
        self.sim.delete_device(device.device)
        device.delete()
        self.devices.remove(device)
