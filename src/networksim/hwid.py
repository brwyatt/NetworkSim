import logging
from random import randbytes
from typing import Optional


logger = logging.getLogger(__name__)


class HWID:
    length_bytes = 6

    def __init__(self, bytes: Optional[bytes] = None):
        self.bytes = bytes

    @property
    def bytes(self):
        return self._bytes

    @bytes.setter
    def bytes(self, value: Optional[bytes]):
        if value is None:
            # Don't accidentally create a broadcast address randomly
            while value is None or value == self.broadcast().bytes:
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

    def __str__(self):
        return ":".join(format(x, "02x") for x in self.bytes)

    @classmethod
    def broadcast(cls):
        if not hasattr(cls, "_broadcast"):
            cls._broadcast = cls(int.to_bytes(255) * cls.length_bytes)
        return cls._broadcast

    def __eq__(self, other):
        return self.bytes == other.bytes
