import logging
from typing import Optional

from networksim.helpers import randbytes


logger = logging.getLogger(__name__)


class Addr:
    length_bytes = 6
    separator = ":"
    base = 16

    def __init__(self, byte_value: Optional[bytes] = None):
        self.byte_value = byte_value

    @property
    def byte_value(self):
        return self._bytes

    @byte_value.setter
    def byte_value(self, value: Optional[bytes]):
        if value is None:
            # Don't accidentally create a broadcast address randomly
            while value is None or value == self.broadcast().byte_value:
                value = randbytes(self.length_bytes)
        elif type(value) is not bytes:
            raise TypeError(
                f"bytes: expected `bytes`, received `{type(value)}`",
            )

        if len(value) > self.length_bytes:
            logger.warn(
                f"bytes: value is longer than {self.length_bytes} and will be truncated",
            )
            value = value[0 : self.length_bytes]
        elif len(value) < self.length_bytes:
            value = bytes(self.length_bytes - len(value)) + value

        self._bytes = value

    @classmethod
    def from_str(cls, macaddr_str: str):
        byte_value = bytes(
            [
                int(x, cls.base).to_bytes(1, "big")[0]
                for x in macaddr_str.split(cls.separator)
            ],
        )

        return cls(byte_value)

    @classmethod
    def broadcast(cls):
        if not hasattr(cls, "_broadcast"):
            cls._broadcast = cls(
                int.to_bytes(255, 1, "big") * cls.length_bytes,
            )
        return cls._broadcast

    def __eq__(self, other) -> bool:
        return self.byte_value == other.byte_value

    def __hash__(self) -> int:
        return int.from_bytes(self.byte_value, "big")