import logging
from typing import Optional

from networksim.hardware.device import Device
from networksim.hardware.port import Port


logger = logging.getLogger(__name__)


class IPDevice(Device):
    def __init__(
        self,
        name: Optional[str] = None,
        port_count: int = 1,
        auto_process: bool = False,
    ):
        super().__init__(name, port_count, auto_process)

    def handle_connection_state_change(self, port: Port):
        super().handle_connection_state_change(port)

    def process_inputs(self):
        for port in self.ports:
            pass
