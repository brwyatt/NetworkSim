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
        process_rate: Optional[int] = None,
    ):
        super().__init__(name, port_count, auto_process, process_rate)

        self.ip = IPStack()

    def handle_connection_state_change(self, port: Port):
        super().handle_connection_state_change(port)
        if not port.connected:
            self.ip.unbind(port=port)

    def run_jobs(self):
        self.ip.addr_table.expire()
        super().run_jobs()

    def process_payload(self, payload, src: HWID, dst: HWID, port: Port):
        if isinstance(payload, self.ip.supported_types):
            self.ip.process_packet(payload, src, dst, port)
