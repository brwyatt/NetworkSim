import logging
from typing import List
from typing import Optional

from networksim.addr.macaddr import MACAddr
from networksim.hardware.device import Device
from networksim.hardware.interface import Interface
from networksim.stack.ipstack import IPStack


logger = logging.getLogger(__name__)


class IPDevice(Device):
    def __init__(
        self,
        name: Optional[str] = None,
        auto_process: bool = True,
        ifaces: Optional[List[Interface]] = None,
        process_rate: Optional[int] = None,
    ):
        super().__init__(
            name=name,
            auto_process=auto_process,
            ifaces=ifaces,
            process_rate=process_rate,
        )

        self.ip = IPStack()

    def step(self):
        super().step()
        self.ip.step()

    def handle_connection_state_change(self, iface: Interface):
        super().handle_connection_state_change(iface)
        if not iface.connected:
            self.ip.unbind(iface=iface)

    def run_jobs(self):
        self.ip.addr_table.expire()
        super().run_jobs()

    def process_payload(
        self,
        payload,
        src: MACAddr,
        dst: MACAddr,
        iface: Interface,
    ):
        if isinstance(payload, self.ip.supported_types):
            self.ip.process_packet(payload, src, dst, iface)
