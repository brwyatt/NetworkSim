import logging
from typing import Optional

from networksim.hardware.device import Device
from networksim.hardware.port import Port
from networksim.hwid import HWID
from networksim.stack.ipstack import IPStack


logger = logging.getLogger(__name__)


class IPDevice(Device):
    def __init__(
        self,
        name: Optional[str] = None,
        port_count: int = 1,
        auto_process: bool = True,
    ):
        super().__init__(name, port_count, auto_process)

        self.ip = IPStack()

    def handle_connection_state_change(self, port: Port):
        super().handle_connection_state_change(port)
        if not port.connected:
            self.ip.unbind(port=port)

    def run_jobs(self):
        self.ip.addr_table.expire()
        super().run_jobs()

    def process_inputs(self):
        for port in self.ports:
            packet = port.receive()
            if packet is None or packet.dst not in [port.hwid, HWID.broadcast()]:
                continue
            if isinstance(packet.payload, self.ip.supported_types):
                self.ip.process_packet(packet.payload)
