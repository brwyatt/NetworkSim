import logging
from typing import Optional
from typing import Union

from networksim.hwid import HWID
from networksim.packet import Packet
from networksim.packet.payload import Payload


logger = logging.getLogger(__name__)


class EthernetPacket(Packet):
    def __init__(
        self,
        dst: Optional[HWID] = None,
        src: Optional[HWID] = None,
        payload: Optional[Union[Packet, Payload, str]] = None,
    ):
        if dst is None:
            dst = HWID.broadcast()
        if not isinstance(dst, HWID):
            raise TypeError(f"dst: expected `HWID` got `{type(dst)}`")

        if src is not None and not isinstance(src, HWID):
            raise TypeError(f"src: expected `HWID` got `{type(src)}`")

        super().__init__(dst, src, payload)
