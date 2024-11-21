import tkinter as tk
from typing import TYPE_CHECKING
from typing import Union

from networksim.hardware.cable import Cable
from networksim.packet import Packet
from networksim.packet.ethernet import EthernetPacket
from networksim.packet.ip import IPPacket
from networksim.packet.ip.icmp import ICMPPacket
from networksim.packet.ip.udp import UDP
from networksim.ui.device_shape import DeviceShape
from networksim.ui.packet_menu import create_packet_menu

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

        self.packet_shapes = []

        self.a.add_update_handler(self.update_location)
        self.b.add_update_handler(self.update_location)

        canvas.tag_bind(self.line, "<ButtonPress-1>", self.left_click)
        canvas.tag_bind(self.line, "<ButtonPress-3>", self.right_click)

        self.raise_shapes()

    def clear_packet_shapes(self):
        for packet_shape in self.packet_shapes:
            self.canvas.delete(packet_shape)

        self.packet_shapes = []

    def get_packet_color(self, packet):
        color = "red"
        if isinstance(packet, EthernetPacket):
            color = "green"
            if isinstance(packet.payload, IPPacket):
                color = "blue"
                if isinstance(packet.payload.payload, UDP):
                    color = "lightblue"
                elif isinstance(packet.payload.payload, ICMPPacket):
                    color = "yellow"
        return color

    def get_packet_click_handler(self, packet: Packet):
        def handler(event):
            self.canvas.last_event = event.serial
            menu = create_packet_menu(self.canvas, packet)
            menu.post(event.x_root, event.y_root)
            self.canvas.menu = menu

            return menu

        return handler

    def draw_packets(self):
        self.clear_packet_shapes()

        ax, ay = self.a.get_midpoint()
        bx, by = self.b.get_midpoint()

        packet_size = 10 * self.canvas.scale_factor

        for i in range(0, self.cable.length):
            ratio = (i + 1) / (self.cable.length + 1)

            for x in range(0, self.cable.bandwidth):
                if self.cable.ab_transit[i][x] is None:
                    # Hit end of packets for this segment
                    break
                ab_x1 = bx + ((ax - bx) * ratio)
                ab_y1 = (
                    by
                    + ((ay - by) * ratio)
                    - (packet_size / 2)
                    + (x * packet_size)
                )
                ab = self.canvas.create_rectangle(
                    ab_x1,
                    ab_y1,
                    ab_x1 + packet_size,
                    ab_y1 + packet_size,
                    fill=self.get_packet_color(self.cable.ab_transit[i][x]),
                )
                self.canvas.tag_bind(
                    ab,
                    "<ButtonPress-1>",
                    self.get_packet_click_handler(self.cable.ab_transit[i][x]),
                )
                self.packet_shapes.append(ab)

            for x in range(0, self.cable.bandwidth):
                if self.cable.ba_transit[i][x] is None:
                    # Hit end of packets for this segment
                    break
                ba_x1 = ax + ((bx - ax) * ratio) - packet_size
                ba_y1 = (
                    ay
                    + ((by - ay) * ratio)
                    - (packet_size / 2)
                    + (x * packet_size)
                )
                ba = self.canvas.create_rectangle(
                    ba_x1,
                    ba_y1,
                    ba_x1 + packet_size,
                    ba_y1 + packet_size,
                    fill=self.get_packet_color(self.cable.ba_transit[i][x]),
                )
                self.canvas.tag_bind(
                    ba,
                    "<ButtonPress-1>",
                    self.get_packet_click_handler(self.cable.ba_transit[i][x]),
                )
                self.packet_shapes.append(ba)

    def update_location(self):
        self.canvas.coords(
            self.line,
            *self.a.get_midpoint(),
            *self.b.get_midpoint(),
        )
        self.draw_packets()

    def delete(self):
        self.a.del_update_handler(self.update_location)
        self.b.del_update_handler(self.update_location)
        self.clear_packet_shapes()
        self.canvas.delete(self.line)

    def raise_shapes(self):
        self.canvas.tag_raise(self.line)

        self.a.raise_shapes()
        self.b.raise_shapes()

        for packet_shape in self.packet_shapes:
            self.canvas.tag_raise(packet_shape)

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
