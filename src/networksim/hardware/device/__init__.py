from collections import defaultdict
from typing import Optional

from networksim.hardware.port import Port
from networksim.helpers import randbytes
from networksim.hwid import HWID


class Device:
    def __init__(self, name: Optional[str] = None, port_count: int = 1):
        self.base_MAC = randbytes(5)
        if name is None:
            name = f"{type(self).__name__}-{self.base_MAC.hex()}"
        self.name = name
        self.ports = []
        self.connection_states = defaultdict(lambda: False)

        for x in range(1, port_count + 1):
            self.add_port(HWID(self.base_MAC + int.to_bytes(x)))

    def add_port(self, hwid: Optional[HWID] = None):
        self.ports.append(Port(hwid))

    def step(self):
        pass
