import logging

from networksim.hardware.port import Port


logger = logging.getLogger(__name__)


class Cable:
    def __init__(self, a: Port = None, b: Port = None, length: int = 3):
        self.a = a
        self.b = b
        self.length = 3

    @property
    def a(self) -> Port:
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

    def flush(self):
        self.ab_transit = [None for x in range(0, 3)]
        self.ba_transit = [None for x in range(0, 3)]

    def step(self):
        if self.a is None or self.b is None:
            self.flush()
            return

        for x in range(0, self.length):
            if x == 0:
                if self.ab_transit[x] is not None:
                    self.b.inbound_write(self.ab_transit[x])
                if self.ba_transit[x] is not None:
                    self.a.inbound_write(self.ba_transit[x])
                continue
            self.ab_transit[x - 1] = self.ab_transit[x]
            self.ba_transit[x - 1] = self.ba_transit[x]

        self.ab_transit[self.length - 1] = self.a.outbound_read()
        self.ba_transit[self.length - 1] = self.b.outbound_read()
