from random import choice
from typing import List
from typing import Optional

import networksim.application.dhcp.payload as payload
from networksim.application import Application
from networksim.hardware.device import Device
from networksim.hardware.interface import Interface
from networksim.hwid import HWID
from networksim.ipaddr import IPAddr
from networksim.ipaddr import IPNetwork
from networksim.packet import Packet
from networksim.packet.ethernet import EthernetPacket
from networksim.packet.ip import IPPacket
from networksim.packet.ip.udp import UDP


class DHCPLease:
    def __init__(self, hwid: HWID, addr: IPAddr, expires: int = 500):
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
        lease_time: int = 5000,
        range_start: Optional[IPAddr] = None,
        range_end: Optional[IPAddr] = None,
        router: Optional[IPAddr] = None,
        nameservers: Optional[List[IPAddr]] = None,
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

        self.router = router
        self.nameservers = nameservers

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

    def checkout(self, hwid: HWID, addr: Optional[IPAddr] = None) -> DHCPLease:
        lease = self.check_lease(hwid, addr)
        if lease is None:
            # No existing lease, only use provided addr if not in use (and provided)
            addr = (
                addr
                if addr is not None and addr in self.pool
                else choice(list(self.pool))
            )
            lease = DHCPLease(hwid, addr, self.lease_time)
        lease.expires = self.lease_time
        self.leases.add(lease)
        try:
            self.pool.remove(lease.addr)
        except KeyError:
            # ignore
            pass

        return lease

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
        iface: Interface,
    ):
        if not isinstance(packet.payload, payload.DHCPPayload):
            self.log.append(
                f"Received invalid packet payload {type(packet.payload)}",
            )
            return

        try:
            bind = self.device.ip.bound_ips.get_binds(
                network=self.network,
                iface=iface,
            )[0]
        except IndexError:
            # Unexpected, until we implement DHCP proxying
            self.log.append(
                "Received DHCP packet on interface not bound to the network we offer DHCP for",
            )
            return

        # set options
        options = {
            1: self.network,
            51: self.lease_time,
            58: int(self.lease_time / 2),
            59: int(self.lease_time * 3 / 4),
        }
        if self.router is not None:
            options[3] = self.router
        if self.nameservers is not None and len(self.nameservers) > 0:
            options[6] = self.nameservers

        if isinstance(packet.payload, payload.DHCPDiscover):
            self.log.append("Received DHCPDiscover")
            req_ip = packet.payload.options.get(50, None)
            lease = self.checkout(packet.payload.client_hwid, req_ip)

            self.log.append("Sending DHCPOffer")
            iface.send(
                EthernetPacket(
                    dst=lease.hwid,
                    src=iface.hwid,
                    payload=IPPacket(
                        dst=lease.addr,
                        src=bind.addr,
                        payload=UDP(
                            dst_port=68,
                            src_port=67,
                            payload=payload.DHCPOffer(
                                your_ip=lease.addr,
                                server_ip=bind.addr,
                                client_hwid=lease.hwid,
                                options=options,
                            ),
                        ),
                    ),
                ),
            )
            return

        if isinstance(packet.payload, payload.DHCPRequest):
            self.log.append("Received DHCPRequest")
            server = packet.payload.options.get(54, packet.payload.server_ip)
            if server != bind.addr:
                self.log.append(
                    f"Client {packet.payload.client_hwid} accepted offer from other "
                    f"DHCP server {server}, instead of ours!",
                )
                lease = self.check_lease(hwid=packet.payload.client_hwid)
                if lease is not None:
                    self.checkin(hwid=lease.hwid, addr=lease.addr)
                return

            lease = self.checkout(
                hwid=packet.payload.client_hwid,
                addr=packet.payload.options.get(50, None),
            )
            if lease.addr != packet.payload.options.get(50, None):
                # how did we get here!? - Probably an explicit request for an address
                # leased to someone else...
                self.log.append(
                    "Unable to accept request for "
                    f"{packet.payload.options.get(50, None)} "
                    f"from {packet.payload.client_hwid}",
                )
                self.checkin(hwid=lease.hwid, addr=lease.addr)
                # send a NACK
                self.log.append("Sending DHCPNack")
                iface.send(
                    EthernetPacket(
                        dst=lease.hwid,
                        src=iface.hwid,
                        payload=IPPacket(
                            dst=lease.addr,
                            src=bind.addr,
                            payload=UDP(
                                dst_port=68,
                                src_port=67,
                                payload=payload.DHCPNack(
                                    server_ip=bind.addr,
                                    client_hwid=lease.hwid,
                                ),
                            ),
                        ),
                    ),
                )

            self.log.append("Sending DHCPAck")
            iface.send(
                EthernetPacket(
                    dst=lease.hwid,
                    src=iface.hwid,
                    payload=IPPacket(
                        dst=lease.addr,
                        src=bind.addr,
                        payload=UDP(
                            dst_port=68,
                            src_port=67,
                            payload=payload.DHCPAck(
                                your_ip=lease.addr,
                                server_ip=bind.addr,
                                client_hwid=lease.hwid,
                                options=options,
                            ),
                        ),
                    ),
                ),
            )
            return
