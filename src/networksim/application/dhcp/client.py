from typing import List

from networksim.application import Application
from networksim.hardware.device import Device
from networksim.hardware.port import Port
from networksim.ipaddr import IPAddr
from networksim.packet import Packet
from networksim.packet.ip.udp import UDP


class DHCPClient(Application):
    def __init__(self, device: Device, *args, **kwargs):
        super().__init__(device, *args, **kwargs)

    def start(self):
        self.device.ip.bind_protocol(
            UDP,
            IPAddr(byte_value=bytes(4)),
            68,
            self.process_packet,
        )

    def stop(self):
        self.device.ip.unbind_protocol(
            UDP,
            IPAddr(byte_value=bytes(4)),
            68,
        )

    def step(self):
        pass

    def process_packet(
        self,
        packet: Packet,
        src: IPAddr,
        dst: IPAddr,
        port: Port,
    ):
        pass
