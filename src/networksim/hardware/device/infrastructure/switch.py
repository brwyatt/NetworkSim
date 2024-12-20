from typing import List
from typing import Optional

from networksim.addr.macaddr import MACAddr
from networksim.hardware.device import Device
from networksim.hardware.interface import Interface
from networksim.packet import Packet


class CAMEntry:
    def __init__(
        self,
        macaddr: MACAddr,
        iface: Interface,
        expiration: int = 200,
    ):
        self.macaddr = macaddr
        self.iface = iface
        self.expiration = expiration

    def __eq__(self, other):
        return (self.macaddr == other.macaddr) and (self.iface == other.iface)


class CAMTable:
    def __init__(self, expiration: int = 200):
        self.table = {}
        self.expiration = expiration

    def add_entry(self, macaddr: MACAddr, iface: Interface):
        entry = CAMEntry(
            macaddr=macaddr,
            iface=iface,
            expiration=self.expiration,
        )
        self.table[entry.macaddr] = entry

    def get_iface(self, macaddr: MACAddr) -> Interface:
        if macaddr not in self.table:
            return None

        return self.table[macaddr].iface

    def get_macaddrs_by_iface(self, iface: Interface) -> List[MACAddr]:
        return [x.macaddr for x in self.table.values() if x.iface == iface]

    def expire(self):
        for macaddr in list(self.table.keys()):
            if macaddr not in self.table:
                continue
            self.table[macaddr].expiration -= 1
            if self.table[macaddr].expiration <= 0:
                self.delete_macaddr(macaddr)

    def delete_macaddr(self, macaddr: MACAddr):
        try:
            del self.table[macaddr]
        except KeyError:
            pass

    def delete_port(self, iface: Interface):
        for macaddr in self.get_macaddrs_by_iface(iface):
            self.delete_macaddr(macaddr)


class Switch(Device):
    default_iface_count = 4

    def __init__(
        self,
        name: Optional[str] = None,
        ifaces: Optional[List[Interface]] = None,
        cam_expire: int = 200,
        process_rate: Optional[int] = None,
    ):
        super().__init__(
            name=name,
            ifaces=ifaces,
            auto_process=True,
            process_rate=process_rate,
        )
        self.CAM = CAMTable(expiration=cam_expire)

    @property
    def forward_capacity(self):
        return self.process_rate

    def handle_connection_state_change(self, iface: Interface):
        super().handle_connection_state_change(iface)
        self.CAM.delete_port(iface)

    def run_jobs(self):
        self.CAM.expire()
        super().run_jobs()

    def process_packet(self, packet: Packet, iface: Interface):
        self.CAM.add_entry(packet.src, iface)

        dst_iface = (
            None
            if packet.dst == MACAddr.broadcast()
            else self.CAM.get_iface(packet.dst)
        )
        if dst_iface is None:
            # Unknown destination or destination is broadcast... flood!
            dst_ifaces = [x for x in self.ifaces if x != iface]
        else:
            dst_ifaces = [dst_iface]

        for dst_iface in dst_ifaces:
            dst_iface.send(packet)
