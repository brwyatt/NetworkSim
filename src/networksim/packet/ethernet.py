import logging
from typing import Optional
from typing import Union

from networksim.addr.macaddr import MACAddr
from networksim.packet import Packet
from networksim.packet.payload import Payload


logger = logging.getLogger(__name__)


class EthernetPacket(Packet):
    def __init__(
        self,
        dst: Optional[MACAddr] = None,
        src: Optional[MACAddr] = None,
        payload: Optional[Union[Packet, Payload, str]] = None,
    ):
        if dst is None:
            dst = MACAddr.broadcast()
        if not isinstance(dst, MACAddr):
            raise TypeError(f"dst: expected `MACAddr` got `{type(dst)}`")

        if src is not None and not isinstance(src, MACAddr):
            raise TypeError(f"src: expected `MACAddr` got `{type(src)}`")

        super().__init__(dst, src, payload)
