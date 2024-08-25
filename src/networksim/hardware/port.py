import logging
from typing import Optional

from networksim.hwid import HWID


logger = logging.getLogger(__name__)


class Port:
    def __init__(self, hwid: Optional[HWID] = None):
        self.hwid = hwid

    @property
    def hwid(self) -> HWID:
        return self._hwid

    @hwid.setter
    def hwid(self, value: Optional[HWID]):
        if value is None:
            value = HWID()
        elif type(value) is not HWID:
            raise TypeError(
                f"hwid: expected `HWID`, received `{type(value)}`",
            )

        self._hwid = value
