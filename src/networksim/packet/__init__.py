import logging


logger = logging.getLogger(__name__)


class Packet:
    def __init__(self, src, dst, payload):
        self.src = src
        self.dst = dst
        self.payload = payload

    def broadcast(self):
        return self.dst == HWID.broadcast()

    def __str__(self):
        return f"{self.src}>{self.dst} => {self.payload}"
