import logging
from enum import Enum
from typing import Optional
from typing import Union

from networksim.packet import Packet
from networksim.packet.payload import Payload


logger = logging.getLogger(__name__)


class ICMP_Type(Enum):
    Echo_Reply = 0
    Echo_Request = 8
    Time_Exceeded = 11


class ICMPPacket(Packet):
    def __init__(
        self,
        message_type: ICMP_Type,
        payload: Optional[Union[Packet, Payload, str]] = None,
    ):
        if not isinstance(message_type, ICMP_Type):
            raise TypeError(
                f"message_type: expected `ICMP_Type` got `{type(message_type)}`",
            )


class ICMPPing(ICMPPacket):
    def __init__(
        self,
        identifier: int,
        sequence: int,
        payload: Optional[Union[Packet, Payload, str]] = None,
    ):
        super().__init__(message_type=ICMP_Type.Echo_Request)

        self.identifier = identifier
        self.sequence = sequence
        self.payload = payload

    def __str__(self):
        return (
            f"ID={self.identifier},SEQ={self.sequence},PAYLOAD={self.payload}"
        )


class ICMPPong(ICMPPacket):
    def __init__(
        self,
        identifier: int,
        sequence: int,
        payload: Optional[Union[Packet, Payload, str]] = None,
    ):
        super().__init__(message_type=ICMP_Type.Echo_Reply)

        self.identifier = identifier
        self.sequence = sequence
        self.payload = payload

    def __str__(self):
        return (
            f"ID={self.identifier},SEQ={self.sequence},PAYLOAD={self.payload}"
        )
