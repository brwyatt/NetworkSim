from random import randint
from typing import Dict

from networksim.application import Application
from networksim.hardware.device import Device
from networksim.hardware.port import Port
from networksim.ipaddr import IPAddr
from networksim.packet import Packet
from networksim.packet.ip.icmp import ICMPPing
from networksim.packet.ip.icmp import ICMPPong


class Ping(Application):
    def __init__(self, device: Device, dst_ip: IPAddr, *args, **kwargs):
        super().__init__(device, *args, **kwargs)

        self.dst_ip = dst_ip
        self.sequence = 0
        self.identifier = randint(0, 65535)

        self.step_count = 0
        self.in_flight: Dict[int, int] = {}  # { seq_id: expire_time }

        self.route = self.device.ip.routes.find_route(dst=self.dst_ip)
        # local destination may be a router!
        self.route_dst = (
            self.dst_ip if self.route.via is None else self.route.via
        )
        self.arp_timer = 0

        self.arp_timeout = 40
        self.ping_timeout = 60

        self.max_in_flight = 1

    def start(self):
        self.device.ip.bind_protocol(
            ICMPPong,
            IPAddr(byte_value=bytes(4)),
            self.identifier,
            self.process_packet,
        )

    def stop(self):
        self.device.ip.unbind_protocol(
            ICMPPong,
            IPAddr(byte_value=bytes(4)),
            self.identifier,
        )

    def step(self):
        self.step_count += 1

        for seq, exp in list(self.in_flight.items()):
            if exp >= self.ping_timeout:
                self.log.append(f"{self.step_count}: Ping timeout (seq={seq})")
                try:
                    del self.in_flight[seq]
                except KeyError:
                    # Shouldn't be possible
                    pass
            else:
                self.in_flight[seq] = exp + 1

        if self.device.ip.addr_table.lookup(self.route_dst) is None:
            if self.arp_timer >= self.arp_timeout:
                self.log.append(
                    f"{self.step_count}: ARP lookup timed out! Host unreachable!",
                )
                self.arp_timer = 0
            if self.arp_timer == 0:
                self.log.append(
                    f"{self.step_count}: Host unknown, sending ARP",
                )
                # Send ARP for local network destination - destination host or router
                self.device.ip.send_arp_request(self.route_dst)
            self.arp_timer += 1
            return

        if len(self.in_flight) < self.max_in_flight:
            self.sequence += 1
            self.log.append(
                f"{self.step_count}: Sending Ping with seq={self.sequence}",
            )
            self.device.ip.send(
                dst=self.dst_ip,
                payload=ICMPPing(
                    identifier=self.identifier,
                    sequence=self.sequence,
                    payload={"time": self.step_count},
                ),
            )
            self.in_flight[self.sequence] = 0

    def process_packet(
        self,
        packet: Packet,
        src: IPAddr,
        dst: IPAddr,
        port: Port,
    ):
        self.log.append(
            f"{self.step_count}: {dst} recieved PONG from {src} seq={packet.sequence}: {self.step_count - packet.payload['time']}",
        )
        try:
            del self.in_flight[packet.sequence]
        except KeyError:
            # Was the received packet from a timed-out request? Or spoofed?
            pass
