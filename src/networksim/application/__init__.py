from typing import List
from typing import Optional

from networksim.addr.ipaddr import IPAddr
from networksim.addr.macaddr import MACAddr
from networksim.hardware.device import Device
from networksim.hardware.interface import Interface
from networksim.packet import Packet


class Application:
    def __init__(self, device: Device, *args, **kwargs):
        self.device = device
        self.log: List[str] = []
        self.step_count = 0

    def start(self):
        pass

    def stop(self):
        pass

    def step(self):
        self.step_count += 1

    def process_packet(
        self,
        packet: Packet,
        src: IPAddr,
        dst: IPAddr,
        iface: Interface,
        hwsrc: Optional[MACAddr] = None,
        hwdst: Optional[MACAddr] = None,
    ):
        pass
