from typing import List

from networksim.hardware.device import Device
from networksim.hardware.interface import Interface
from networksim.ipaddr import IPAddr
from networksim.packet import Packet


class Application:
    def __init__(self, device: Device, *args, **kwargs):
        self.device = device
        self.log: List[str] = []

    def start(self):
        pass

    def stop(self):
        pass

    def step(self):
        pass

    def process_packet(
        self,
        packet: Packet,
        src: IPAddr,
        dst: IPAddr,
        iface: Interface,
    ):
        pass
