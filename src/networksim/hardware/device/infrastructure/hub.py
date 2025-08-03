from typing import List
from typing import Optional

from networksim.hardware.device import Device
from networksim.hardware.interface import Interface
from networksim.packet import Packet


class Hub(Device):
    default_iface_count = 4

    def __init__(
        self,
        name: Optional[str] = None,
        ifaces: Optional[List[Interface]] = None,
        process_rate: Optional[int] = None,
    ):
        super().__init__(
            name=name,
            ifaces=ifaces,
            auto_process=True,
            process_rate=process_rate,
        )

    @property
    def forward_capacity(self):
        return self.process_rate

    def handle_connection_state_change(self, iface: Interface):
        super().handle_connection_state_change(iface)

    def run_jobs(self):
        super().run_jobs()

    def process_packet(self, packet: Packet, iface: Interface):
        for dst_iface in [x for x in self.ifaces if x != iface]:
            dst_iface.send(packet)
