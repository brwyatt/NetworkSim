import logging
from bisect import insort
from typing import Optional

from networksim.hardware.port import Port
from networksim.hwid import HWID
from networksim.ipaddr import IPAddr, IPNetwork
from networksim.stack import Stack


logger = logging.getLogger(__name__)


class ARPEntry:
    def __init__(self, addr: IPAddr, hwid: HWID, expiration: int = 100):
        self.addr = addr
        self.hwid = hwid
        self.exipration = expiration

    def __eq__(self, other):
        return (self.addr == other.addr) and (self.hwid == self.hwid)


class ARPTable:
    def __init__(self, expiration: int = 100):
        self.table = {}
        self.expiration = expiration

    def add_entry(self, addr: IPAddr, hwid: HWID):
        entry = ARPEntry(addr=addr, hwid=hwid, expiration=self.expiration)
        self.table[entry.addr] = entry

    def expire(self):
        for addr in list(self.table.keys()):
            if addr not in self.table:
                continue
            self.table[addr].expiration -= 1
            if self.table[addr].expiration <= 0:
                self.delete_addr(addr)

    def delete_addr(self, addr: IPAddr):
        try:
            del self.table[addr]
        except KeyError:
            pass

    def lookup(self, addr: IPAddr):
        if addr not in self.table:
            return None
        return self.table[addr].hwid


class Route:
    def __init__(
        self,
        network: IPNetwork,
        port: Port,
        via: Optional[IPAddr] = None,
        src: Optional[IPAddr] = None,
    ):
        self.network = network
        self.port = port
        self.via = via
        self.src = src

    def __lt__(self, other):
        return self.network.match_bits < other.network.match_bits

    def __hash__(self):
        return hash((self.network, self.port, self.via, self.src))

    def __str__(self):
        via = f" via {self.via}" if self.via is not None else ""
        src = f" src {self.src}" if self.src is not None else ""
        return f"{self.network}{via} dev {self.port.hwid}{src}"


class RouteTable:
    def __init__(self):
        self.routes = []

    def add_route(
        self,
        network: IPNetwork,
        port: Port,
        via: Optional[IPAddr] = None,
        src: Optional[IPAddr] = None,
    ):
        route = Route(network, port, via, src)
        insort(self.routes, route)

    def del_routes(
        self,
        network: Optional[IPNetwork] = None,
        port: Optional[Port] = None,
        via: Optional[IPAddr] = None,
        src: Optional[IPAddr] = None,
    ):
        self.routes = [
            x for x in self.routes
            if not (
                (network is None or network == x.network) and
                (port is None or port == x.port) and
                (via is None or via == x.via) and
                (src is None or src == x.src)
            )
        ]

    def find_route(self, dst: IPAddr) -> Optional[Route]:
        found_route = None

        for route in self.routes:
            if route.network.in_network(dst):
                found_route = route

        return found_route


class IPStack(Stack):
    def __init__(self):
        super().__init__()
        self.addr_table = ARPTable()
        self.routes = RouteTable()
