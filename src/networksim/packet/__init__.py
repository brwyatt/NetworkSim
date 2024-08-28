import logging


logger = logging.getLogger(__name__)


class Packet:
    def __init__(self, dst, src, payload):
        self.dst = dst
        self.src = src
        self.payload = payload

    def __str__(self):
        return f"{self.src}>{self.dst} => {self.payload}"
