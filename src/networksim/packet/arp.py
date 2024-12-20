import logging
from typing import Optional

from networksim.addr.ipaddr import IPAddr
from networksim.addr.macaddr import MACAddr
from networksim.packet import Packet


logger = logging.getLogger(__name__)


class ARPPacket(Packet):
    def __init__(
        self,
        dst: Optional[MACAddr] = None,
        dst_ip: Optional[IPAddr] = None,
        src: Optional[MACAddr] = None,
        src_ip: Optional[IPAddr] = None,
        request: bool = True,
    ):
        if dst is not None and not isinstance(dst, MACAddr):
            raise TypeError(f"dst: expected `MACAddr` got `{type(dst)}`")
        self.dst = dst

        if dst_ip is not None and not isinstance(dst_ip, IPAddr):
            raise TypeError(f"dst_ip: expected `IPAddr` got `{type(dst_ip)}`")
        self.dst_ip = dst_ip

        if src is not None and not isinstance(src, MACAddr):
            raise TypeError(f"src: expected `MACAddr` got `{type(src)}`")
        self.src = src

        if src_ip is not None and not isinstance(src_ip, IPAddr):
            raise TypeError(f"src_ip: expected `IPAddr` got `{type(src_ip)}`")
        self.src_ip = src_ip

        self.request = request

    def __str__(self):
        return f"{self.src}({self.src_ip})>{self.dst}({self.dst_ip})"
