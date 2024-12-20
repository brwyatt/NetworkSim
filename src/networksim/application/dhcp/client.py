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
from networksim.stack.ipstack import IPBind


class DHCPClient(Application):
    default_route = IPNetwork(
        addr=IPAddr(byte_value=bytes(IPAddr.length_bytes)),
        match_bits=0,
    )

    def __init__(
        self,
        device: Device,
        *args,
        ifaces: Optional[List[Interface]] = None,
        **kwargs,
    ):
        super().__init__(device, *args, **kwargs)

        if ifaces is None:
            ifaces = device.ifaces
        self.ifaces = ifaces

        self.timeout = 60

        self.leases = {}
        for iface in self.ifaces:
            if iface not in self.leases:
                self.leases[iface] = {}
                self.init_iface(iface)

        self.arp_requests = {}

    def start(self):
        self.device.ip.bind_protocol(
            UDP,
            IPAddr(byte_value=bytes(4)),
            68,
            self.process_packet,
        )

    def stop(self):
        self.device.ip.unbind_protocol(
            UDP,
            IPAddr(byte_value=bytes(4)),
            68,
        )

    def init_iface(self, iface: Interface):
        self.leases[iface]["state"] = "INIT"
        self.leases[iface]["request-timeout"] = 0
        self.leases[iface]["renew"] = 0
        self.leases[iface]["rebind"] = 0
        self.leases[iface]["expire"] = 0
        if self.leases[iface].get("bind", None) is not None:
            self.device.ip.unbind(
                addr=self.leases[iface]["bind"].addr,
                iface=iface,
            )
            self.device.ip.routes.del_routes(
                network=self.default_route,
                iface=iface,
            )
        self.leases[iface]["bind"] = None
        self.leases[iface]["server"] = None
        self.leases[iface]["router"] = None
        self.leases[iface]["nameservers"] = None

        return self.leases[iface]

    def step(self):
        super().step()

        for arp, expire in list(self.arp_requests.items()):
            self.arp_requests[arp] = expire - 1
            if expire <= 0:
                del self.arp_requests[arp]

        for iface, lease in self.leases.items():
            lease["renew"] = 0 if lease["renew"] == 0 else lease["renew"] - 1
            lease["rebind"] = (
                0 if lease["rebind"] == 0 else lease["rebind"] - 1
            )
            lease["expire"] = (
                0 if lease["expire"] == 0 else lease["expire"] - 1
            )
            lease["request-timeout"] = (
                0
                if lease["request-timeout"] == 0
                else lease["request-timeout"] - 1
            )

            if not iface.connected:
                # Set next state (when it connects)
                lease["state"] = (
                    "INIT-REBOOT"
                    if lease["bind"] is not None and lease["expire"] > 0
                    else "INIT"
                )
                lease["request-timeout"] = 0
                # ... and skip
                continue

            # State transitions based on timers
            if lease["state"] == "BOUND" and lease["renew"] <= 0:
                # We were in renewing state when rebinding timer expired
                lease["state"] = "RENEWING"
                lease["request-timeout"] = 0
            elif lease["state"] == "RENEWING" and lease["rebind"] <= 0:
                # We were in renewing state when rebinding timer expired
                lease["state"] = "REBINDING"
                lease["request-timeout"] = 0
            elif lease["state"] == "REBINDING" and lease["expire"] <= 0:
                # We were in rebinding when lease expired
                self.init_iface(iface)

            if lease["request-timeout"] > 0 or lease["state"] == "BOUND":
                # requests in-flight, or lease is active
                continue

            # Send messages based on states and timers
            if lease["state"] in ["INIT-REBOOT", "SELECTING", "REBINDING"]:
                # We're init-reboot/selecting/rebinding, and either haven't sent a request or previous request timed out

                options = {
                    50: lease["bind"].addr,
                }
                if lease["server"] is not None:
                    options[54] = lease["server"]

                self.log.append(
                    f"{self.step_count}: Sending DHCPRequest for {lease['bind'].addr} ({lease['state']})",
                )
                iface.send(
                    EthernetPacket(
                        dst=HWID.broadcast(),
                        src=iface.hwid,
                        payload=IPPacket(
                            dst=IPAddr.broadcast(),
                            src=IPAddr(byte_value=bytes(IPAddr.length_bytes)),
                            payload=UDP(
                                dst_port=67,
                                src_port=68,
                                payload=payload.DHCPRequest(
                                    client_hwid=iface.hwid,
                                    server_ip=lease["server"],
                                    options=options,
                                ),
                            ),
                        ),
                    ),
                )
                lease["request-timeout"] = self.timeout
            elif lease["state"] == "INIT":
                # We're init, and either haven't sent a discover or previous discover timed out
                options = {}
                if lease["bind"] is not None:
                    # Request last IP, if available
                    options[50] = lease["bind"].addr

                self.log.append(
                    f"{self.step_count}: Sending DHCPDiscover ({lease['state']})",
                )
                iface.send(
                    EthernetPacket(
                        dst=HWID.broadcast(),
                        src=iface.hwid,
                        payload=IPPacket(
                            dst=IPAddr.broadcast(),
                            src=IPAddr(byte_value=bytes(IPAddr.length_bytes)),
                            payload=UDP(
                                dst_port=67,
                                src_port=68,
                                payload=payload.DHCPDiscover(
                                    client_hwid=iface.hwid,
                                    options=options,
                                ),
                            ),
                        ),
                    ),
                )
                lease["request-timeout"] = self.timeout
            elif lease["state"] == "RENEWING":
                # We're in renewing state, and either haven't sent a request or previous request timed out
                # This is different from other states, as we send Unicast, instead of broadcast

                options = {
                    50: lease["bind"].addr,
                }
                if lease["server"] is not None:
                    options[54] = lease["server"]

                dst_hwid = self.device.ip.addr_table.lookup(lease["server"])
                if dst_hwid is None:
                    # send ARP request if we haven't already, then wait and try again
                    if self.arp_requests.get(lease["server"], 0) <= 0:
                        self.device.ip.send_arp_request(lease["server"])
                    continue

                self.log.append(
                    f"{self.step_count}: Sending DHCPRequest for {lease['bind'].addr} ({lease['state']})",
                )
                iface.send(
                    EthernetPacket(
                        dst=dst_hwid,
                        src=iface.hwid,
                        payload=IPPacket(
                            dst=lease["server"],
                            src=lease["bind"].addr,
                            payload=UDP(
                                dst_port=67,
                                src_port=68,
                                payload=payload.DHCPRequest(
                                    client_hwid=iface.hwid,
                                    server_ip=lease["server"],
                                    options=options,
                                ),
                            ),
                        ),
                    ),
                )
                lease["request-timeout"] = self.timeout

    def process_packet(
        self,
        packet: Packet,
        src: IPAddr,
        dst: IPAddr,
        iface: Interface,
        hwsrc: Optional[HWID] = None,
        hwdst: Optional[HWID] = None,
    ):
        if not isinstance(packet.payload, payload.DHCPPayload):
            self.log.append(
                f"{self.step_count} ({src}): Received invalid packet payload {type(packet.payload)}",
            )
            return

        lease = self.leases.get(iface)
        if lease is None:
            self.log.append(
                f"{self.step_count} ({src}): Received DCHP packet on interface we don't care about",
            )
            return

        if isinstance(packet.payload, payload.DHCPNack):
            self.log.append(
                f"{self.step_count} ({src}): Received DHCPNack for {dst} ({lease['state']})",
            )
            if lease["state"] in ["INIT-REBOOT", "RENEWING", "REBINDING"]:
                self.init_iface(iface)
            return

        if isinstance(packet.payload, payload.DHCPOffer):
            self.log.append(
                f"{self.step_count} ({src}): Received DHCPOffer for {packet.payload.your_ip} ({lease['state']})",
            )
            if lease["state"] != "INIT":
                self.log.append(
                    f"{self.step_count} ({src}): Received DHCP OFFER when not in valid state",
                )
                return

            if packet.payload.client_hwid != iface.hwid:
                self.log.append(
                    f"{self.step_count} ({src}): Received DCHP OFFER not for us!",
                )
                return

            bind = IPBind(
                addr=packet.payload.your_ip,
                network=packet.payload.options.get(
                    1,
                    IPNetwork(
                        addr=packet.payload.your_ip,
                        match_bits=24,
                    ),  # assume /24
                ),
                iface=iface,
            )

            # We don't need to send here, as it's handled in step(), we just need to set the right states
            lease["state"] = "SELECTING"
            lease["bind"] = bind
            lease["request-timeout"] = 0
            lease["expire"] = packet.payload.options.get(51, 500)
            lease["renew"] = packet.payload.options.get(
                58,
                int(lease["expire"] / 2),
            )
            lease["rebind"] = packet.payload.options.get(
                59,
                int(lease["expire"] * 3 / 4),
            )
            lease["server"] = packet.payload.options.get(
                54,
                packet.payload.server_ip,
            )
            lease["router"] = packet.payload.options.get(3)
            lease["nameservers"] = packet.payload.options.get(6)

        if isinstance(packet.payload, payload.DHCPAck):
            self.log.append(
                f"{self.step_count} ({src}): Received DHCPAck for {packet.payload.your_ip} ({lease['state']})",
            )
            if lease["state"] not in [
                "INIT-REBOOT",
                "SELECTING",
                "RENEWING",
                "REBINDING",
            ]:
                self.log.append(
                    f"{self.step_count} ({src}): Received DHCP ACK when not in valid state",
                )
                return

            if packet.payload.client_hwid != iface.hwid:
                self.log.append(
                    f"{self.step_count} ({src}): Received DCHP Ack not for us!",
                )
                return

            bind = IPBind(
                addr=packet.payload.your_ip,
                network=packet.payload.options.get(
                    1,
                    IPNetwork(
                        addr=packet.payload.your_ip,
                        match_bits=24,
                    ),  # assume /24
                ),
                iface=iface,
            )

            if bind != lease["bind"]:
                # Something is very wrong, the ACK we gont isn't for what we have or were offered!
                self.log.append(
                    f"{self.step_count} ({src}): Received DHCP ACK that doesn't match previous OFFER or existing lease",
                )
                return

            self.device.ip.bind(
                addr=bind.addr,
                network=bind.network,
                iface=iface,
            )
            lease["state"] = "BOUND"
            lease["request-timeout"] = 0
            lease["expire"] = packet.payload.options.get(51, 500)
            lease["renew"] = packet.payload.options.get(
                58,
                int(lease["expire"] / 2),
            )
            lease["rebind"] = packet.payload.options.get(
                59,
                int(lease["expire"] * 3 / 4),
            )
            lease["server"] = packet.payload.options.get(
                54,
                packet.payload.server_ip,
            )

            lease["router"] = packet.payload.options.get(3)
            if lease["router"] is not None:
                self.device.ip.routes.add_route(
                    self.default_route,
                    iface,
                    via=lease["router"],
                )

            lease["nameservers"] = packet.payload.options.get(6)
