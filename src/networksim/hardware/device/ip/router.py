import logging
from typing import Optional

from networksim.hardware.device.ip.ipdevice import IPDevice
from networksim.hardware.interface import Interface
from networksim.hwid import HWID
from networksim.stack.ipstack import IPStack


logger = logging.getLogger(__name__)


class Router(IPDevice):
    def __init__(
        self,
        name: Optional[str] = None,
        iface_count: int = 2,
        auto_process: bool = True,
        process_rate: Optional[int] = None,
    ):
        super().__init__(name, iface_count, auto_process, process_rate)

        self.ip = IPStack(forward_packets=True)

    def process_payload(self, payload, src: HWID, dst: HWID, iface: Interface):
        if isinstance(payload, self.ip.supported_types):
            self.ip.process_packet(payload, src, dst, iface)
