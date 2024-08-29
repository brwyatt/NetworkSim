import logging
from bisect import insort
from collections import namedtuple
from typing import List, Optional, Union

from networksim.hardware.port import Port
from networksim.hwid import HWID
from networksim.ipaddr import IPAddr, IPNetwork
from networksim.packet.arp import ARPPacket
from networksim.packet.ethernet import EthernetPacket
from networksim.packet.ip import IPPacket
from networksim.stack import Stack


logger = logging.getLogger(__name__)


class ARPEntry:
    def __init__(self, addr: IPAddr, hwid: HWID, expiration: int = 100):
        self.addr = addr
        self.hwid = hwid
        self.expiration = expiration

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
        if route not in self.routes:
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


IPBind = namedtuple("IPBind", ["addr", "network", "port"])


class BoundIPs:
    def __init__(self):
        self.binds = []

    def add_bind(self, addr: IPAddr, network: IPNetwork, port: Port):
        bind = IPBind(addr, network, port)
        if bind not in self.binds:
            self.binds.append(bind)

    def get_binds(
        self,
        addr: Optional[IPAddr] = None,
        network: Optional[IPNetwork] = None,
        port: Optional[Port] = None,
    ) -> List[IPBind]:
        return [
            x for x in self.binds
            if (
                (addr is None or addr == x.addr) and
                (network is None or network == x.network) and
                (port is None or port == x.port)
            )
        ]

    def del_binds(
        self,
        addr: Optional[IPAddr] = None,
        network: Optional[IPNetwork] = None,
        port: Optional[Port] = None,
    ) -> List[IPBind]:
        self.binds = [
            x for x in self.binds
            if not (
                (addr is None or addr == x.addr) and
                (network is None or network == x.network) and
                (port is None or port == x.port)
            )
        ]


class IPStack(Stack):
    def __init__(self, arp_expire: int = 100):
        super().__init__()
        self.addr_table = ARPTable(arp_expire)
        self.routes = RouteTable()
        self.bound_ips = BoundIPs()
        self.arp_expire = arp_expire

    @property
    def supported_types(self) -> List[type]:
        return [ARPPacket, IPPacket]

    def bind(self, addr: IPAddr, network: IPNetwork, port: Port):
        self.bound_ips.add_bind(addr, network, port)
        self.routes.add_route(network, port, src=addr)
        self.send_garp(addr, port)

    def unbind(
        self,
        addr: Optional[IPAddr],
        port: Optional[Port],
    ):
        self.bound_ips.del_binds(addr=addr, port=port)
        self.routes.del_routes(src=addr, port=port)

    def send_arp_request(self, addr: IPAddr):
        route = self.routes.find_route(addr)
        if route is None or route.src is None or route.port is None:
            logger.error(f"Could not find suitible route for {addr}")
            return

        route.port.send(
            EthernetPacket(
                dst=HWID.broadcast(),
                src=route.port.hwid,
                payload = ARPPacket(
                    dst_ip=addr,
                    src=route.port.hwid,
                    src_ip=route.src,
                    request=True,
                ),
            )
        )

    def send_arp_response(self, dst: IPAddr, src: IPAddr, port: Optional[Port] = None):
        if port is None:
            try:
                port = [
                    x for x in self.bound_ips.get_binds(addr=src)
                    if x.port is not None
                ][:1][0].port
            except IndexError:
                logger.error(f"Could not find bound port for {src}")
                return

        dst_hwid = self.addr_table.lookup(dst)

        port.send(
            EthernetPacket(
                dst=dst_hwid,
                src=port.hwid,
                payload = ARPPacket(
                    dst=dst_hwid,
                    dst_ip=dst,
                    src=port.hwid,
                    src_ip=src,
                    request=False,
                ),
            )
        )

    def send_garp(self, addr: IPAddr, port: Optional[Port]):
        if port is None:
            try:
                port = [
                    x for x in self.bound_ips.get_binds(addr=addr)
                    if x.port is not None
                ][:1][0].port
            except IndexError:
                logger.error(f"Could not find bound port for {addr}")
                return

        port.send(
            EthernetPacket(
                dst=HWID.broadcast(),
                src=port.hwid,
                payload = ARPPacket(
                    dst_ip=addr,  # silly, but it is how it is defined
                    src=port.hwid,
                    src_ip=addr,
                    request=False,
                ),
            )
        )

    def process_arp(self, packet: ARPPacket):
        if packet.src is not None and packet.src_ip is not None:
            # Anything that gives something we can map
            self.addr_table.add_entry(packet.src_ip, packet.src)

            if packet.request and packet.dst is None and packet.dst_ip is not None:
                # ARP Request
                if len(self.bound_ips.get_binds(addr=packet.dst_ip)):
                    # ARP if for one of our IPs, respond
                    self.send_arp_response(dst=packet.src_ip, src=packet.dst_ip)


    def process_packet(self, packet: Union[ARPPacket, IPPacket]):
        self.addr_table.expire()
        if type(packet) is ARPPacket:
            self.process_arp(packet)
