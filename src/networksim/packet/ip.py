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
        payload = None,
    ):
        if type(dst) is not HWID:
            logger.error(f"dst: expected `IPAddr` got `{type(dst)}`")

        if src is not None and type(src) is not HWID:
            logger.error(f"src: expected `IPAddr` got `{type(src)}`")

        super().__init__(dst, src, payload)
