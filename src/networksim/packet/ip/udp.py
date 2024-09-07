from typing import Optional

from networksim.packet import Packet


class UDP(Packet):
    def __init__(self, src_port: int, dst_port: int, payload: Optional = None):
        self.src_port = src_port
        self.dst_port = dst_port
        self.payload = payload
