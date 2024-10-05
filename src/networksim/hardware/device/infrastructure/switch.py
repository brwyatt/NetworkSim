from typing import List
from typing import Optional

from networksim.hardware.device import Device
from networksim.hardware.interface import Interface
from networksim.hwid import HWID
from networksim.packet import Packet


class CAMEntry:
    def __init__(self, hwid: HWID, iface: Interface, expiration: int = 200):
        self.hwid = hwid
        self.iface = iface
        self.expiration = expiration

    def __eq__(self, other):
        return (self.hwid == other.hwid) and (self.iface == other.iface)


class CAMTable:
    def __init__(self, expiration: int = 200):
        self.table = {}
        self.expiration = expiration

    def add_entry(self, hwid: HWID, iface: Interface):
        entry = CAMEntry(hwid=hwid, iface=iface, expiration=self.expiration)
        self.table[entry.hwid] = entry

    def get_iface(self, hwid: HWID) -> Interface:
        if hwid not in self.table:
            return None

        return self.table[hwid].iface

    def get_hwids_by_iface(self, iface: Interface) -> List[HWID]:
        return [x.hwid for x in self.table.values() if x.iface == iface]

    def expire(self):
        for hwid in list(self.table.keys()):
            if hwid not in self.table:
                continue
            self.table[hwid].expiration -= 1
            if self.table[hwid].expiration <= 0:
                self.delete_hwid(hwid)

    def delete_hwid(self, hwid: HWID):
        try:
            del self.table[hwid]
        except KeyError:
            pass

    def delete_port(self, iface: Interface):
        for hwid in self.get_hwids_by_iface(iface):
            self.delete_hwid(hwid)


class Switch(Device):
    def __init__(
        self,
        name: Optional[str] = None,
        iface_count: int = 4,
        cam_expire: int = 200,
        forward_capacity: Optional[int] = None,
    ):
        super().__init__(
            name=name,
            iface_count=iface_count,
            auto_process=True,
            process_rate=forward_capacity,
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
            if packet.dst == HWID.broadcast()
            else self.CAM.get_iface(packet.dst)
        )
        if dst_iface is None:
            # Unknown destination or destination is broadcast... flood!
            dst_ifaces = [x for x in self.ifaces if x != iface]
        else:
            dst_ifaces = [dst_iface]

        for dst_iface in dst_ifaces:
            dst_iface.send(packet)
