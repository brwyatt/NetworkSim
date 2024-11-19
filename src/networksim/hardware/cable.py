import logging

from networksim.hardware.interface import Interface
from networksim.serializer import Serializable


logger = logging.getLogger(__name__)


class Cable(Serializable):
    def __init__(
        self,
        a: Interface = None,
        b: Interface = None,
        length: int = 3,
        max_bandwidth: int = 1,
    ):
        self.length = length
        self.max_bandwidth = max_bandwidth
        self.a = a
        self.b = b

    @property
    def a(self) -> Interface:
        if not hasattr(self, "_a"):
            return None
        return self._a

    @a.setter
    def a(self, iface: Interface):
        if hasattr(self, "_b") and self._a:
            self._a.disconnect()

        if iface is None:
            self._a = None
        elif iface and type(iface) is Interface:
            iface.connect()
            self._a = iface

        self.flush()

    @property
    def b(self) -> Interface:
        if not hasattr(self, "_b"):
            return None
        return self._b

    @b.setter
    def b(self, iface: Interface):
        if hasattr(self, "_b") and self._b:
            self._b.disconnect()

        if iface is None:
            self._b = None
        elif iface and type(iface) is Interface:
            iface.connect()
            self._b = iface

        self.flush()

    @property
    def bandwidth(self):
        return min(
            min(
                self.max_bandwidth,
                (
                    self.a.max_bandwidth
                    if self.a is not None
                    else self.max_bandwidth
                ),
            ),
            self.b.max_bandwidth if self.b is not None else self.max_bandwidth,
        )

    def flush(self):
        self.ab_transit = [
            tuple([None for x in range(0, self.bandwidth)])
            for x in range(0, self.length)
        ]
        self.ba_transit = [
            tuple([None for x in range(0, self.bandwidth)])
            for x in range(0, self.length)
        ]

    def step(self):
        if self.a is None or self.b is None:
            self.flush()
            return

        for x in range(0, self.length):
            if x == 0:
                for packet in self.ab_transit[x]:
                    if packet is not None:
                        self.b.inbound_write(packet)
                for packet in self.ba_transit[x]:
                    if packet is not None:
                        self.a.inbound_write(packet)
                continue
            self.ab_transit[x - 1] = self.ab_transit[x]
            self.ba_transit[x - 1] = self.ba_transit[x]

        self.ab_transit[self.length - 1] = tuple(
            [self.a.outbound_read() for _ in range(self.bandwidth)],
        )
        self.ba_transit[self.length - 1] = tuple(
            [self.b.outbound_read() for _ in range(self.bandwidth)],
        )
