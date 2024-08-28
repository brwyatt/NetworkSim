import logging


logger = logging.getLogger(__name__)


class IPAddr:
    length_octets = 4
    length_bytes = 8 * length_octets

    def __init__(self, byte_value: bytes):
        self.byte_value = byte_value

