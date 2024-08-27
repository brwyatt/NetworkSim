import logging
from collections import defaultdict
from typing import Optional

from networksim.hardware.port import Port
from networksim.helpers import randbytes
from networksim.hwid import HWID


logger = logging.getLogger(__name__)


class Device:
    def __init__(self, name: Optional[str] = None, port_count: int = 1):
        self.base_MAC = randbytes(5)
        if name is None:
            name = f"{type(self).__name__}-{self.base_MAC.hex()}"
        self.name = name
        self.ports = []
        self.connection_states = defaultdict(lambda: False)

        for x in range(1, port_count + 1):
            self.add_port(HWID(self.base_MAC + int.to_bytes(x, 1, "big")))

    def add_port(self, hwid: Optional[HWID] = None):
        self.ports.append(Port(hwid))

    def process_payload(self, payload):
        logger.info(payload)

    def step(self):
        for port in self.ports:
            packet = port.receive()
            if packet is not None:
                if packet.dst not in [port.hwid, HWID.broadcast()]:
                    logger.info(
                        f"Ignoring packet from {packet.src} for {packet.dst} (not us!)"
                    )
                    continue
                logger.info(
                    f"Received {'broadcast' if packet.broadcast() else 'unicast'} "
                    f"packet from {packet.src}"
                )
                self.process_payload(packet.payload)

    def __getitem__(self, index):
        return self.ports[index]

    def port_id(self, port: Port):
        return self.ports.index(port)
