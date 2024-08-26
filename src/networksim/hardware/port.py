import logging
from queue import Empty
from queue import Full
from queue import Queue
from typing import Optional

from networksim.hwid import HWID
from networksim.packet import Packet


logger = logging.getLogger(__name__)


class Port:
    def __init__(self, hwid: Optional[HWID] = None, queue_length: int = 3):
        self.connected = False
        self.hwid = hwid
        self.inbound_queue = Queue(queue_length)
        self.outbound_queue = Queue(queue_length)

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

    def outbound_write(self, packet: Packet):
        if not self.connected:
            return

        try:
            self.outbound_queue.put(packet, block=False)
        except Full:
            logger.warn(
                "Failed to enqueue packet to Outbound Queue: Queue full!",
            )

    def outbound_read(self) -> Optional[Packet]:
        try:
            packet = self.outbound_queue.get(block=False)
        except Empty:
            logger.info(
                "Failed to dequeue packet from Outbound Queue: Queue empty!",
            )
            return None

        self.outbound_queue.task_done()
        return packet

    def outbound_flush(self):
        try:
            while not self.outbound_queue.empty():
                self.outbound_queue.get(block=False)
        except Empty:
            pass

    def inbound_write(self, packet: Packet):
        try:
            self.inbound_queue.put(packet, block=False)
        except Full:
            logger.warn(
                "Failed to enqueue packet to Inbound Queue: Queue full!",
            )

    def inbound_read(self) -> Optional[Packet]:
        try:
            packet = self.inbound_queue.get(block=False)
        except Empty:
            logger.info(
                "Failed to dequeue packet from Inbound Queue: Queue empty!",
            )
            return None

        self.inbound_queue.task_done()
        return packet

    def inbound_flush(self):
        try:
            while not self.inbound_queue.empty():
                self.inbound_queue.get(block=False)
        except Empty:
            pass

    def send(self, packet: Packet):
        self.outbound_write(packet)

    def receive(self) -> Optional[Packet]:
        return self.inbound_read()

    def connect(self):
        self.connected = True

    def disconnect(self):
        self.outbound_flush()
        self.connected = False
