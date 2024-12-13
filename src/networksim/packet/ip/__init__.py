import logging
from typing import Optional
from typing import Union

from networksim.ipaddr import IPAddr
from networksim.packet import Packet
from networksim.packet.payload import Payload


logger = logging.getLogger(__name__)


class IPPacket(Packet):
    def __init__(
        self,
        dst: IPAddr,
        src: Optional[IPAddr] = None,
        ttl: Optional[int] = None,
        payload: Optional[Union[Packet, Payload, str]] = None,
    ):
        if not isinstance(dst, IPAddr):
            raise TypeError(f"dst: expected `IPAddr` got `{type(dst)}`")

        if src is not None and not isinstance(src, IPAddr):
            raise TypeError(f"src: expected `IPAddr` got `{type(src)}`")

        if ttl is not None and not isinstance(ttl, int):
            raise TypeError(f"ttl: expected `int` got `{type(src)}`")
        self.ttl = ttl if ttl is not None else 10

        super().__init__(dst, src, payload)
