import math
import tkinter as tk
from typing import TYPE_CHECKING

from networksim.hardware.cable import Cable
from networksim.packet.ethernet import EthernetPacket
from networksim.packet.ip import IPPacket
from networksim.packet.ip.icmp import ICMPPacket
from networksim.packet.ip.udp import UDP
from networksim.ui.device_shape import DeviceShape

if TYPE_CHECKING:
    from networksim.ui.viewpane import ViewPane


class CableDrawShape:
    def __init__(
        self,
        canvas: "ViewPane",
        device_a: DeviceShape,
    ):
        self.canvas = canvas
        self.a = device_a

        start_x, start_y = self.a.get_midpoint()

        self.line = self.canvas.create_line(
            start_x,
            start_y,
            start_x,
            start_y,
            width=5,
            fill="red",
        )

        self.motion_bind = canvas.bind("<Motion>", self.update_location)

        self.raise_shapes()
        self.update_location()

    def update_location(self, event=None):
        start_x, start_y = self.a.get_midpoint()

        x = self.canvas.winfo_toplevel().winfo_pointerx()
        y = self.canvas.winfo_toplevel().winfo_pointery()

        if event is not None:
            x = event.x
            y = event.y

        x = self.canvas.canvasx(x)
        y = self.canvas.canvasy(y)

        dx = x - start_x
        dy = y - start_y

        length = math.sqrt(dx**2 + dy**2)
        if length > 0:  # Avoid division by zero
            dx = (dx / length) * 5
            dy = (dy / length) * 5

        self.canvas.coords(
            self.line,
            start_x,
            start_y,
            x - dx,
            y - dy,
        )

    def delete(self):
        self.canvas.unbind("<Motion>", self.motion_bind)
        self.canvas.delete(self.line)

    def raise_shapes(self):
        self.canvas.tag_raise(self.line)

        self.a.raise_shapes()
