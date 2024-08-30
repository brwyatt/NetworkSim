import logging
from typing import Optional

from networksim.packet import Packet
from networksim.ipaddr import IPAddr


logger = logging.getLogger(__name__)


class IPPacket(Packet):
    def __init__(
        self,
        dst: IPAddr,
        src: Optional[IPAddr] = None,
        ttl: int = 10,
        payload: Optional = None,
    ):
        if not isinstance(dst, IPAddr):
            raise TypeError(f"dst: expected `IPAddr` got `{type(dst)}`")

        if src is not None and not isinstance(src, IPAddr):
            raise TypeError(f"src: expected `IPAddr` got `{type(src)}`")

        if not isinstance(ttl, int):
            raise TypeError(f"ttl: expected `int` got `{type(src)}`")
        self.ttl = ttl

        super().__init__(dst, src, payload)
