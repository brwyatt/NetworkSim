import logging
from random import randbytes
from typing import Optional


logger = logging.getLogger(__name__)


class Port:
    hwid_length_bytes = 6

    def __init__(self, hwid: Optional[bytes] = None):
        self.hwid = hwid

    @property
    def hwid(self):
        return self._hwid

    @hwid.setter
    def hwid(self, value: Optional[bytes]):
        if value is None:
            value = randbytes(self.hwid_length_bytes)
        elif type(value) is not bytes:
            raise TypeError(
                f"hwid: expected `bytes`, received `{type(value)}`",
            )

        if len(value) > self.hwid_length_bytes:
            logger.warn(
                f"hwid: value is longer than {self.hwid_length_bytes} and will be truncated",
            )
            value = value[0 : self.hwid_length_bytes]
        elif len(value) < self.hwid_length_bytes:
            value = bytes(self.hwid_length_bytes - len(value)) + value

        self._hwid = value

    @property
    def hwid_as_str(self):
        return ":".join(format(x, "02x") for x in self.hwid)
