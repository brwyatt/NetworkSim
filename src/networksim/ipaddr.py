import logging


logger = logging.getLogger(__name__)


class IPAddr:
    length_bytes = 4

    def __init__(self, byte_value: bytes):
        self.byte_value = byte_value

    @classmethod
    def broadcast(cls) -> bytes:
        return cls(
            byte_value=bytes(
                [255 for _ in range(0, IPAddr.length_bytes)],
            ),
        )

    @property
    def byte_value(self) -> bytes:
        return self._byte_value

    @byte_value.setter
    def byte_value(self, byte_value):
        if (
            type(byte_value) is not bytes
            or len(byte_value) != self.length_bytes
        ):
            raise ValueError("Address is not bytes or wrong length!")

        self._byte_value = byte_value

    @classmethod
    def from_str(cls, addr_str: str):
        byte_value = bytes(
            [int(x).to_bytes(1, "big")[0] for x in addr_str.split(".")],
        )

        return cls(byte_value)

    def __str__(self) -> str:
        return ".".join([str(x) for x in self.byte_value])

    def __eq__(self, other) -> bool:
        return self.byte_value == other.byte_value

    def __hash__(self) -> int:
        return int.from_bytes(self.byte_value, "big")


class IPNetwork:
    def __init__(self, addr: IPAddr, match_bits: int = 24):
        if match_bits > (IPAddr.length_bytes * 8):
            raise ValueError("match_bits is greater than address length!")
        self.match_bits = match_bits
        self.mask_bytes = (
            ((2**match_bits) - 1) << ((IPAddr.length_bytes * 8) - match_bits)
        ).to_bytes(IPAddr.length_bytes, "big")

        self.addr = self.apply_mask(addr)

    def apply_mask(self, addr: IPAddr) -> IPAddr:
        return IPAddr(
            byte_value=bytes(
                [
                    x & y
                    for x, y in zip(
                        addr.byte_value[::-1],
                        self.mask_bytes[::-1],
                    )
                ][::-1],
            ),
        )

    @property
    def broadcast_addr(self) -> IPAddr:
        return IPAddr(
            byte_value=bytes(
                [
                    x | (~y + 256)
                    for x, y in zip(
                        self.addr.byte_value[::-1],
                        self.mask_bytes[::-1],
                    )
                ][::-1],
            ),
        )

    def in_network(self, addr: IPAddr):
        return self.addr == self.apply_mask(addr)

    @classmethod
    def default(cls):
        if not hasattr(cls, "_default"):
            cls._default = cls(IPAddr(bytes(IPAddr.length_bytes)), 0)
        return cls._default

    def __str__(self) -> str:
        return f"{self.addr}/{self.match_bits}"

    def __eq__(self, other) -> bool:
        return self.addr == other.addr and self.match_bits == other.match_bits

    def __hash__(self) -> int:
        return hash((self.addr, self.match_bits))
