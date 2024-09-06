from random import choice
from typing import List
from typing import Optional

from networksim.application import Application
from networksim.hardware.device import Device
from networksim.hardware.port import Port
from networksim.hwid import HWID
from networksim.ipaddr import IPAddr
from networksim.ipaddr import IPNetwork
from networksim.packet import Packet
from networksim.packet.ip.udp import UDP


class DHCPLease:
    def __init__(self, hwid: HWID, addr: IPAddr, expires: int = 250):
        self.hwid = hwid
        self.addr = addr
        self.expires = expires

    def __eq__(self, other):
        return self.addr == other.addr and self.hwid == other.hwid

    def __hash__(self):
        return hash((self.addr, self.hwid))


class DHCPServer(Application):
    def __init__(
        self,
        device: Device,
        network: IPNetwork,
        *args,
        lease_time: int = 250,
        range_start: Optional[IPAddr] = None,
        range_end: Optional[IPAddr] = None,
        **kwargs,
    ):
        super().__init__(device, *args, **kwargs)
        if range_start is None:
            range_start = IPAddr(
                byte_value=int.to_bytes(
                    int.from_bytes(network.addr.byte_value, "big")
                    + int(
                        (2 ** ((IPAddr.length_bytes * 8) - network.match_bits))
                        * 0.1,
                    ),
                    IPAddr.length_bytes,
                    "big",
                ),
            )
        if range_end is None:
            range_end = IPAddr(
                byte_value=int.to_bytes(
                    int.from_bytes(network.broadcast_addr.byte_value, "big")
                    - int(
                        (2 ** ((IPAddr.length_bytes * 8) - network.match_bits))
                        * 0.1,
                    ),
                    IPAddr.length_bytes,
                    "big",
                ),
            )

        if not network.in_network(range_start):
            raise ValueError(
                f"Start of range {range_start} not in network {network}",
            )
        if not network.in_network(range_end):
            raise ValueError(
                f"Start of range {range_end} not in network {network}",
            )

        self.network = network
        self.range_start = range_start
        self.range_end = range_end

        self.pool = set()
        for x in range(
            int.from_bytes(range_start.byte_value, "big"),
            int.from_bytes(range_end.byte_value, "big"),
        ):
            self.pool.add(
                IPAddr(byte_value=int.to_bytes(x, IPAddr.length_bytes, "big")),
            )

        self.lease_time = lease_time

        self.leases = set()

    def check_lease(
        self,
        hwid: Optional[HWID] = None,
        addr: Optional[IPAddr] = None,
    ):
        leases = [
            x
            for x in self.leases
            if (hwid is None or x.hwid == hwid)
            and (addr is None or x.addr == addr)
        ]
        if len(leases) == 0:
            return None
        return leases[0]

    def checkout(self, hwid: HWID, addr: Optional[IPAddr] = None):
        lease = self.check_lease(hwid, addr)
        if lease is None:
            addr = addr if addr is not None else choice(self.pool)
            lease = DHCPLease(hwid, addr, self.lease_time)
        lease.expires = self.lease_time
        self.leases.add(lease)
        try:
            self.pool.remove(lease.addr)
        except KeyError:
            # ignore
            pass

    def checkin(self, hwid, addr):
        try:
            self.leases.remove(DHCPLease(hwid, addr, 0))
        except KeyError:
            pass

        if self.check_lease(addr=addr) is None:
            self.pool.add(addr)

    def start(self):
        self.device.ip.bind_protocol(
            UDP,
            IPAddr(byte_value=bytes(4)),
            67,
            self.process_packet,
        )

    def stop(self):
        self.device.ip.unbind_protocol(
            UDP,
            IPAddr(byte_value=bytes(4)),
            67,
        )

    def step(self):
        for x in list(self.leases):
            if x.expires == 0:
                self.checkin(x.hwid, x.addr)
                continue
            x.expires -= 1

    def process_packet(
        self,
        packet: Packet,
        src: IPAddr,
        dst: IPAddr,
        port: Port,
    ):
        pass
