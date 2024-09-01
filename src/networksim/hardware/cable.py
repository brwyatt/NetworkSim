import logging

from networksim.hardware.port import Port


logger = logging.getLogger(__name__)


class Cable:
    def __init__(
        self,
        a: Port = None,
        b: Port = None,
        length: int = 3,
        max_bandwidth: int = 1,
    ):
        self.length = length
        self.max_bandwidth = max_bandwidth
        self.a = a
        self.b = b

    @property
    def a(self) -> Port:
        if not hasattr(self, "_a"):
            return None
        return self._a

    @a.setter
    def a(self, port: Port):
        if hasattr(self, "_b") and self._a:
            self._a.disconnect()

        if port is None:
            self._a = None
        elif port and type(port) is Port:
            port.connect()
            self._a = port

        self.flush()

    @property
    def b(self) -> Port:
        if not hasattr(self, "_b"):
            return None
        return self._b

    @b.setter
    def b(self, port: Port):
        if hasattr(self, "_b") and self._b:
            self._b.disconnect()

        if port is None:
            self._b = None
        elif port and type(port) is Port:
            port.connect()
            self._b = port

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
