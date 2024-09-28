import logging
from bisect import insort
from collections import namedtuple
from typing import Callable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from networksim.hardware.port import Port
from networksim.hwid import HWID
from networksim.ipaddr import IPAddr
from networksim.ipaddr import IPNetwork
from networksim.packet.arp import ARPPacket
from networksim.packet.ethernet import EthernetPacket
from networksim.packet.ip import IPPacket
from networksim.packet.ip.icmp import ICMPPacket
from networksim.packet.ip.icmp import ICMPPing
from networksim.packet.ip.icmp import ICMPPong
from networksim.packet.ip.udp import UDP
from networksim.stack import Stack


logger = logging.getLogger(__name__)


class ARPEntry:
    def __init__(self, addr: IPAddr, hwid: HWID, expiration: int = 250):
        self.addr = addr
        self.hwid = hwid
        self.expiration = expiration

    def __eq__(self, other):
        return (self.addr == other.addr) and (self.hwid == self.hwid)


class ARPTable:
    def __init__(self, expiration: int = 250):
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

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

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
            x
            for x in self.routes
            if not (
                (network is None or network == x.network)
                and (port is None or port == x.port)
                and (via is None or (x.via is not None and via == x.via))
                and (src is None or (x.src is not None and src == x.src))
            )
        ]

    def find_route(
        self,
        dst: IPAddr,
        src: Optional[IPAddr] = None,
        port: Optional[Port] = None,
    ) -> Optional[Route]:
        found_route = None

        for route in self.routes:
            if (
                route.network.in_network(dst)
                and (src is None or route.src is None or route.src == src)
                and (port is None or route.port == port)
            ):
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
            x
            for x in self.binds
            if (
                (addr is None or addr == x.addr)
                and (network is None or network == x.network)
                and (port is None or port == x.port)
            )
        ]

    def del_binds(
        self,
        addr: Optional[IPAddr] = None,
        network: Optional[IPNetwork] = None,
        port: Optional[Port] = None,
    ) -> List[IPBind]:
        self.binds = [
            x
            for x in self.binds
            if not (
                (addr is None or addr == x.addr)
                and (network is None or network == x.network)
                and (port is None or port == x.port)
            )
        ]


QueuedSend = namedtuple(
    "QueuedSend",
    ["pending", "dst", "payload", "src", "port", "ttl"],
)


class ProtocolAlreadyBoundException(Exception):
    pass


class IPStack(Stack):
    def __init__(self, arp_expire: int = 250, forward_packets: bool = False):
        super().__init__()
        self.forward_packets = forward_packets
        self.addr_table = ARPTable(arp_expire)
        self.routes = RouteTable()
        self.bound_ips = BoundIPs()
        self.arp_expire = arp_expire
        self.protocol_binds = {}
        self.arp_request_timeout = 40
        self.arp_requests = {}
        self.send_queue = []

    @property
    def supported_types(self) -> Tuple[type]:
        return (ARPPacket, IPPacket)

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

    def bind_protocol(
        self,
        packet_type: type,
        addr: IPAddr,
        port: int,
        callback: Callable,
    ):
        if (packet_type, addr, port) in self.protocol_binds:
            raise ProtocolAlreadyBoundException(
                f"Handler already bound for {packet_type} on {addr}:{port}!",
            )

        self.protocol_binds[(packet_type, addr, port)] = callback

    def unbind_protocol(self, packet_type: type, addr: IPAddr, port: int):
        try:
            del self.protocol_binds[(packet_type, addr, port)]
        except KeyError:
            pass

    def step(self):
        for addr, timer in list(self.arp_requests.items()):
            if timer <= 0:
                del self.arp_requests[addr]
                # Just delete/clear the queue, but should send errors back
                self.send_queue = [x for x in self.send_queue if x.dst != addr]
                continue
            self.arp_requests[addr] = timer - 1

    def get_protocol_callback(
        self,
        packet_type: type,
        addr: IPAddr,
        port: int,
    ) -> Optional[Callable]:
        return self.protocol_binds.get(
            (packet_type, addr, port),
            self.protocol_binds.get(
                (packet_type, IPAddr(byte_value=bytes(4)), port),
                None,
            ),
        )

    def send_arp_request(self, addr: IPAddr, force: bool = False):
        route = self.routes.find_route(addr)
        if route is None or route.src is None or route.port is None:
            logger.error(f"Could not find suitible route for {addr}")
            return

        if addr in self.arp_requests:
            logger.warning(f"ARP already in-flight for {addr}!")
            if not force:
                return

        route.port.send(
            EthernetPacket(
                dst=HWID.broadcast(),
                src=route.port.hwid,
                payload=ARPPacket(
                    dst_ip=addr,
                    src=route.port.hwid,
                    src_ip=route.src,
                    request=True,
                ),
            ),
        )

        self.arp_requests[addr] = self.arp_request_timeout

    def send_arp_response(
        self,
        dst: IPAddr,
        src: IPAddr,
        port: Optional[Port] = None,
    ):
        if port is None:
            try:
                port = [
                    x
                    for x in self.bound_ips.get_binds(addr=src)
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
                payload=ARPPacket(
                    dst=dst_hwid,
                    dst_ip=dst,
                    src=port.hwid,
                    src_ip=src,
                    request=False,
                ),
            ),
        )

    def send_garp(self, addr: IPAddr, port: Optional[Port] = None):
        if port is None:
            try:
                port = [
                    x
                    for x in self.bound_ips.get_binds(addr=addr)
                    if x.port is not None
                ][:1][0].port
            except IndexError:
                logger.error(f"Could not find bound port for {addr}")
                return

        port.send(
            EthernetPacket(
                dst=HWID.broadcast(),
                src=port.hwid,
                payload=ARPPacket(
                    dst_ip=addr,  # silly, but it is how it is defined
                    src=port.hwid,
                    src_ip=addr,
                    request=False,
                ),
            ),
        )

    def send(
        self,
        dst: IPAddr,
        payload,
        src: Optional[IPAddr] = None,
        port: Optional[Port] = None,
        ttl: Optional[int] = None,
    ):
        src_bind = None
        if src is not None:
            try:
                src_bind = self.bound_ips.get_binds(
                    addr=src,
                    port=port,
                )[0].addr
            except IndexError:
                # no bound IP matches, so ignore - might be routing or spoofing
                pass

        route = self.routes.find_route(dst, src=src_bind, port=port)
        next_hop = route.via if route is not None else None
        if next_hop is not None:
            route = self.routes.find_route(next_hop, src=src_bind, port=port)

        if route is None:
            logger.error(f"No route to {dst}!")
            return

        next_hop = next_hop if next_hop is not None else dst

        src = route.src if src is None else src
        port = route.port
        dst_hwid = self.addr_table.lookup(next_hop)

        if dst_hwid is None:
            logger.error(
                f"Unknown host {next_hop}! -- sending ARP and queing!",
            )
            self.send_arp_request(next_hop)
            self.send_queue.append(
                QueuedSend(
                    pending=next_hop,
                    dst=dst,
                    payload=payload,
                    src=src,
                    port=port,
                    ttl=ttl,
                ),
            )
            return

        port.send(
            EthernetPacket(
                dst=dst_hwid,
                src=port.hwid,
                payload=IPPacket(
                    dst=dst,
                    src=src,
                    payload=payload,
                    ttl=ttl,
                ),
            ),
        )

    def local_source(
        self,
        src_ip: IPAddr,
        port: Optional[Port] = None,
    ) -> bool:
        # Just checks that the reviced packet is from a local network
        src_route = self.routes.find_route(src_ip)
        if src_route is None:
            return False
        if (
            (port is None or src_route.port == port)
            and src_route.src is not None
            and src_route.network is not None
            and self.bound_ips.get_binds(
                src_route.src,
                src_route.network,
                port,
            )
        ):
            # Packet was received on the port we expect for that network (if given), and we have a bound IP for that network on that port. Basically, guards against packets on the wrong network/port overwriting the HWID of an IP in the ARP table on another network/port.
            return True
        return False

    def add_arp(self, src_ip: IPAddr, src: HWID, port: Optional[Port] = None):
        if self.local_source(src_ip, port):
            self.addr_table.add_entry(src_ip, src)
            try:
                del self.arp_requests[src_ip]
            except KeyError:
                # Not something we were waiting on, so we can skip processing the queue
                return
            # attempt to resend any packets waiting on ARPs
            for queued in [x for x in self.send_queue if x.pending == src_ip]:
                self.send_queue.remove(queued)
                self.send(
                    dst=queued.dst,
                    payload=queued.payload,
                    src=queued.src,
                    port=queued.port,
                    ttl=queued.ttl,
                )

    def process_arp(
        self,
        packet: ARPPacket,
        src: Optional[HWID] = None,
        dst: Optional[HWID] = None,
        port: Optional[Port] = None,
    ):
        if packet.src is not None and packet.src_ip is not None:
            # Anything that gives something we can map
            self.add_arp(packet.src_ip, packet.src, port)

            if (
                packet.request
                and packet.dst is None
                and packet.dst_ip is not None
            ):
                # ARP Request
                if len(self.bound_ips.get_binds(addr=packet.dst_ip)):
                    # ARP is for one of our IPs, respond
                    self.send_arp_response(
                        dst=packet.src_ip,
                        src=packet.dst_ip,
                    )

    def process_icmp(
        self,
        packet: ICMPPacket,
        src: IPAddr,
        dst: IPAddr,
        port: Optional[Port] = None,
    ):
        if isinstance(packet, ICMPPing):
            if not self.bound_ips.get_binds(addr=dst, port=port):
                logger.warn(f"Received ping for {dst} from {src} - Not us!")
                return
            self.send(
                dst=src,
                src=dst,
                payload=ICMPPong(
                    identifier=packet.identifier,
                    sequence=packet.sequence,
                    payload=packet.payload,
                ),
                port=port,
            )
            return
        if isinstance(packet, ICMPPong):
            if not self.bound_ips.get_binds(addr=dst, port=port):
                logger.warn(f"Received pong for {dst} from {src} - Not us!")
                return
            logger.info(
                f"Reveiced pong: {packet.identifier} - {packet.sequence}",
            )
            callback = self.get_protocol_callback(
                ICMPPong,
                dst,
                packet.identifier,
            )
            if callback is not None:
                callback(packet, src=src, dst=dst, port=port)

    def process_udp(
        self,
        packet: ICMPPacket,
        src: IPAddr,
        dst: IPAddr,
        port: Optional[Port] = None,
    ):
        callback = self.get_protocol_callback(
            UDP,
            dst,
            packet.dst_port,
        )
        if callback is not None:
            callback(packet, src=src, dst=dst, port=port)

    def process_packet(
        self,
        packet: Union[ARPPacket, IPPacket, UDP],
        src: Optional[HWID] = None,
        dst: Optional[HWID] = None,
        port: Optional[Port] = None,
    ):
        if isinstance(packet, ARPPacket):
            self.process_arp(packet, src, dst, port)
            return

        if not isinstance(packet, IPPacket):
            logger.warning("Received non-IP packet!")
            return

        self.add_arp(packet.src, src, port)

        if (
            self.bound_ips.get_binds(
                port=port,
            )  # don't forward if we don't have an IP
            and packet.dst
            not in (
                [IPAddr.broadcast()]
                + [
                    x.network.broadcast_addr
                    for x in self.bound_ips.get_binds()
                ]
            )  # Filter out broadcast packets
            and not self.bound_ips.get_binds(
                addr=packet.dst,
            )  # Filter out self
        ):
            logger.info(f"Recieved packet for {dst} - Not us!")
            if self.forward_packets:
                logger.info("Forwarding packet!")
                if packet.ttl <= 0:
                    logger.warning("Dropping packet with TTL of 0")
                    return
                self.send(
                    dst=packet.dst,
                    payload=packet.payload,
                    src=packet.src,
                    ttl=packet.ttl - 1,
                )
            return

        if isinstance(packet.payload, ICMPPacket):
            self.process_icmp(
                packet=packet.payload,
                src=packet.src,
                dst=packet.dst,
                port=port,
            )

        if isinstance(packet.payload, UDP):
            self.process_udp(
                packet=packet.payload,
                src=packet.src,
                dst=packet.dst,
                port=port,
            )
