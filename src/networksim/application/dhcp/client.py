from typing import List

import networksim.application.dhcp.payload as payload
from networksim.application import Application
from networksim.hardware.device import Device
from networksim.hardware.port import Port
from networksim.hwid import HWID
from networksim.ipaddr import IPAddr
from networksim.ipaddr import IPNetwork
from networksim.packet import Packet
from networksim.packet.ethernet import EthernetPacket
from networksim.packet.ip import IPPacket
from networksim.packet.ip.udp import UDP
from networksim.stack.ipstack import IPBind


class DHCPClient(Application):
    def __init__(
        self,
        device: Device,
        *args,
        ports: List[Port] = None,
        **kwargs,
    ):
        super().__init__(device, *args, **kwargs)

        if ports is None:
            ports = device.ports
        self.ports = ports

        self.timeout = 50

        self.leases = {}
        for port in ports:
            if port not in self.leases:
                self.leases[port] = {}
                self.init_port(port)

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

    def init_port(self, port: Port):
        self.leases[port]["state"] = "INIT"
        self.leases[port]["request-timeout"] = 0
        self.leases[port]["renew"] = 0
        self.leases[port]["rebind"] = 0
        self.leases[port]["expire"] = 0
        if self.leases[port].get("bind", None) is not None:
            self.device.ip.unbind(
                addr=self.leases[port]["bind"].addr,
                port=port,
            )
        self.leases[port]["bind"] = None
        self.leases[port]["server"] = None

        return self.leases[port]

    def step(self):
        for arp, expire in list(self.arp_requests.items()):
            self.arp_requests[arp] = expire - 1
            if expire <= 0:
                del self.arp_requests[arp]

        for port, lease in self.leases.items():
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

            if not port.connected:
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
                self.init_port(port)

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

                self.log.append(f"Sending DHCPRequest ({lease['state']})")
                port.send(
                    EthernetPacket(
                        dst=HWID.broadcast(),
                        src=port.hwid,
                        payload=IPPacket(
                            dst=IPAddr(
                                byte_value=bytes(
                                    [
                                        255
                                        for _ in range(0, IPAddr.length_bytes)
                                    ],
                                ),
                            ),
                            src=IPAddr(byte_value=bytes(IPAddr.length_bytes)),
                            payload=UDP(
                                dst_port=67,
                                src_port=68,
                                payload=payload.DHCPRequest(
                                    client_hwid=port.hwid,
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

                self.log.append(f"Sending DHCPDiscover ({lease['state']})")
                port.send(
                    EthernetPacket(
                        dst=HWID.broadcast(),
                        src=port.hwid,
                        payload=IPPacket(
                            dst=IPAddr(
                                byte_value=bytes(
                                    [
                                        255
                                        for _ in range(0, IPAddr.length_bytes)
                                    ],
                                ),
                            ),
                            src=IPAddr(byte_value=bytes(IPAddr.length_bytes)),
                            payload=UDP(
                                dst_port=67,
                                src_port=68,
                                payload=payload.DHCPDiscover(
                                    client_hwid=port.hwid,
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

                self.log.append(f"Sending DHCPRequest ({lease['state']})")
                port.send(
                    EthernetPacket(
                        dst=dst_hwid,
                        src=port.hwid,
                        payload=IPPacket(
                            dst=lease["server"],
                            src=lease["bind"].addr,
                            payload=UDP(
                                dst_port=67,
                                src_port=68,
                                payload=payload.DHCPRequest(
                                    client_hwid=port.hwid,
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
        port: Port,
    ):
        if not isinstance(packet.payload, payload.DHCPPayload):
            self.log.append(
                f"Received invalid packet payload {type(packet.payload)}",
            )
            return

        lease = self.leases.get(port)
        if lease is None:
            self.log.append("Received DCHP packet on port we don't care about")
            return

        if isinstance(packet.payload, payload.DHCPNack):
            self.log.append(f"Received DHCPNack ({lease['state']})")
            if lease["state"] in ["INIT-REBOOT", "RENEWING", "REBINDING"]:
                self.init_port(port)
            return

        if isinstance(packet.payload, payload.DHCPOffer):
            self.log.append(f"Received DHCPOffer ({lease['state']})")
            if lease["state"] != "INIT":
                self.log.append("Received DHCP OFFER when not in valid state")
                return

            if packet.payload.client_hwid != port.hwid:
                self.log.append("Received DCHP OFFER not for us!")
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
                port=port,
            )

            # We don't need to send here, as it's handled in step(), we just need to set the right states
            lease["state"] = "SELECTING"
            lease["bind"] = bind
            lease["request-timeout"] = 0
            lease["expire"] = (packet.payload.options.get(51, 500),)
            lease["renew"] = (
                packet.payload.options.get(58, int(lease["expire"] / 2)),
            )
            lease["rebind"] = (
                packet.payload.options.get(59, int(lease["expire"] * 3 / 4)),
            )
            lease["server"] = packet.payload.options.get(
                54,
                packet.payload.server_ip,
            )

        if isinstance(packet.payload, payload.DHCPAck):
            self.log.append(f"Received DHCPAck ({lease['state']})")
            if lease["state"] not in [
                "INIT-REBOOT",
                "SELECTING",
                "RENEWING",
                "REBINDING",
            ]:
                self.log.append("Received DHCP ACK when not in valid state")
                return

            if packet.payload.client_hwid != port.hwid:
                self.log.append("Received DCHP Ack not for us!")
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
                port=port,
            )

            if bind != lease["bind"]:
                # Something is very wrong, the ACK we gont isn't for what we have or were offered!
                self.log.append(
                    "Received DHCP ACK that doesn't match previous OFFER or existing lease",
                )
                return

            self.device.ip.bind(
                addr=bind.addr,
                network=bind.network,
                port=port,
            )
            lease["state"] = "BOUND"
            lease["request-timeout"] = 0
            lease["expire"] = (packet.payload.options.get(51, 500),)
            lease["renew"] = (
                packet.payload.options.get(58, int(lease["expire"] / 2)),
            )
            lease["rebind"] = (
                packet.payload.options.get(59, int(lease["expire"] * 3 / 4)),
            )
            lease["server"] = packet.payload.options.get(
                54,
                packet.payload.server_ip,
            )
