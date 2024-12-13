from typing import Optional
from typing import Union

from networksim.packet import Packet
from networksim.packet.payload import Payload


class UDP(Packet):
    def __init__(
        self,
        src_port: int,
        dst_port: int,
        payload: Optional[Union[Packet, Payload, str]] = None,
    ):
        self.src_port = src_port
        self.dst_port = dst_port
        self.payload = payload

    def __str__(self):
        return f"{self.src_port}>{self.dst_port} => {self.payload}"
