import logging
from collections import defaultdict
from typing import Optional

from networksim.hardware.port import Port
from networksim.helpers import randbytes
from networksim.hwid import HWID


logger = logging.getLogger(__name__)


class Device:
    def __init__(
        self,
        name: Optional[str] = None,
        port_count: int = 1,
        auto_process: bool = False,
    ):
        self.base_MAC = randbytes(5)
        if name is None:
            name = f"{type(self).__name__}-{self.base_MAC.hex()}"
        self.name = name
        self.ports = []
        self.connection_states = defaultdict(lambda: False)
        self.auto_process = auto_process

        for x in range(1, port_count + 1):
            self.add_port(HWID(self.base_MAC + int.to_bytes(x, 1, "big")))

    def add_port(self, hwid: Optional[HWID] = None):
        self.ports.append(Port(hwid))

    def handle_connection_state_change(self, port: Port):
        pass

    def check_connection_state_changes(self):
        for port in self.ports:
            if self.connection_states[port] != port.connected:
                # Connection state has changed!
                self.connection_states[port] = port.connected
                self.handle_connection_state_change(port)

    def process_payload(self, payload):
        logger.info(payload)

    def process_inputs(self):
        for port in self.ports:
            packet = port.receive()
            if packet is not None:
                if packet.dst not in [port.hwid, HWID.broadcast()]:
                    logger.info(
                        f"Ignoring packet from {packet.src} for {packet.dst} (not us!)",
                    )
                    continue
                logger.info(
                    "Received "
                    + (
                        "broadcast"
                        if packet.dst == HWID.broadcast()
                        else "unicast"
                    )
                    + f" packet from {packet.src}",
                )
                self.process_payload(packet.payload)

    def run_jobs(self):
        pass

    def step(self):
        self.check_connection_state_changes()
        self.run_jobs()
        if self.auto_process:
            self.process_inputs()

    def __getitem__(self, index):
        return self.ports[index]

    def port_id(self, port: Port):
        return self.ports.index(port)
