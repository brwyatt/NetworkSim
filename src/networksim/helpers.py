import random


def randbytes_from_randbits(length: int):
    return bytes(bytearray(random.getrandbits(8) for _ in range(0, length)))


if hasattr(random, "randbytes"):
    randbytes = random.randbytes
else:
    randbytes = randbytes_from_randbits
