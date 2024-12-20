import logging
from typing import Optional

from networksim.addr import Addr
from networksim.helpers import randbytes


logger = logging.getLogger(__name__)


class MACAddr(Addr):
    length_bytes = 6

    def __str__(self):
        return self.separator.join(format(x, "02x") for x in self.byte_value)
