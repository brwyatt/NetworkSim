import logging
from typing import Optional

from networksim.hwid import HWID
from networksim.packet.ethernet import EthernetPacket


logger = logging.getLogger(__name__)


class AlreadyConnectedException(Exception):
    pass


class Port:
    def __init__(
        self,
        hwid: Optional[HWID] = None,
        queue_length: int = 3,
        max_bandwidth: int = 1,
    ):
        self.connected = False
        self.hwid = hwid
        self._queue_length = queue_length
        self.max_bandwidth = max_bandwidth
        self.inbound_queue = []
        self.outbound_queue = []

    @property
    def bandwidth(self):
        # Probably need some way to find out the real negotiated bandwidth...
        return self.max_bandwidth

    @property
    def queue_length(self):
        return self._queue_length * self.bandwidth

    @property
    def hwid(self) -> HWID:
        return self._hwid

    @hwid.setter
    def hwid(self, value: Optional[HWID]):
        if value is None:
            value = HWID()
        elif type(value) is not HWID:
            raise TypeError(
                f"hwid: expected `HWID`, received `{type(value)}`",
            )

        self._hwid = value

    def outbound_write(self, packet: EthernetPacket):
        if not self.connected:
            return

        self.outbound_queue = (self.outbound_queue + [packet])[
            0 : self.queue_length
        ]

    def outbound_read(self) -> Optional[EthernetPacket]:
        try:
            packet = self.outbound_queue[0]
            self.outbound_queue = self.outbound_queue[1 : self.queue_length]
        except IndexError:
            logger.debug(
                "Failed to dequeue packet from Outbound Queue: Queue empty!",
            )
            return None

        if packet.src is None:
            packet.src = self.hwid

        return packet

    def outbound_flush(self):
        self.outbound_queue = []

    def inbound_write(self, packet: EthernetPacket):
        self.inbound_queue = (self.inbound_queue + [packet])[
            0 : self.queue_length
        ]

    def inbound_read(self) -> Optional[EthernetPacket]:
        try:
            packet = self.inbound_queue[0]
            self.inbound_queue = self.inbound_queue[1 : self.queue_length]
        except IndexError:
            logger.debug(
                "Failed to dequeue packet from Inbound Queue: Queue empty!",
            )
            return None

        return packet

    def inbound_flush(self):
        self.inbound_queue = []

    def send(self, packet: EthernetPacket):
        self.outbound_write(packet)

    def receive(self) -> Optional[EthernetPacket]:
        return self.inbound_read()

    def connect(self):
        if self.connected:
            raise AlreadyConnectedException()
        self.connected = True

    def disconnect(self):
        self.outbound_flush()
        self.connected = False

    def __hash__(self):
        return self.hwid.__hash__()
