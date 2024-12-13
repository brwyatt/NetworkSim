import logging
from typing import Any
from typing import Optional
from typing import Union

from networksim.packet.payload import Payload


logger = logging.getLogger(__name__)


class Packet:
    def __init__(
        self,
        dst: Any,
        src: Any,
        payload: Optional[Union["Packet", Payload]] = None,
    ):
        self.dst = dst
        self.src = src
        self.payload = payload

    def __str__(self):
        return f"{self.src}>{self.dst} => {self.payload}"
