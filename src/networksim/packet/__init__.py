import logging

from networksim.hwid import HWID


logger = logging.getLogger(__name__)


class Packet:
    def __init__(self, src: HWID, dst: HWID, payload):
        if type(src) is not HWID:
            logger.error(f"src: expected `HWID` got `{type(HWID)}`")
        self.src = src
        if type(dst) is not HWID:
            logger.error(f"dst: expected `HWID` got `{type(HWID)}`")
        self.dst = dst
        self.payload = payload

    def __str__(self):
        return f'{self.src} -> {self.dst} = "{self.payload}"'
