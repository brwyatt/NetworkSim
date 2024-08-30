import logging
from typing import Optional

from networksim.packet import Packet
from networksim.hwid import HWID


logger = logging.getLogger(__name__)


class EthernetPacket(Packet):
    def __init__(
        self,
        dst: Optional[HWID] = None,
        src: Optional[HWID] = None,
        payload = None,
    ):
        if dst is None:
            dst = HWID.broadcast()
        if not isinstance(dst, HWID):
            raise TypeError(f"dst: expected `HWID` got `{type(dst)}`")

        if src is not None and not isinstance(src, HWID):
            raise TypeError(f"src: expected `HWID` got `{type(src)}`")

        super().__init__(dst, src, payload)
