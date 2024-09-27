from typing import List
from typing import Optional

from networksim.hardware.device import Device
from networksim.hardware.port import Port
from networksim.hwid import HWID
from networksim.packet import Packet


class CAMEntry:
    def __init__(self, hwid: HWID, port: Port, expiration: int = 200):
        self.hwid = hwid
        self.port = port
        self.expiration = expiration

    def __eq__(self, other):
        return (self.hwid == other.hwid) and (self.port == other.port)


class CAMTable:
    def __init__(self, expiration: int = 200):
        self.table = {}
        self.expiration = expiration

    def add_entry(self, hwid: HWID, port: Port):
        entry = CAMEntry(hwid=hwid, port=port, expiration=self.expiration)
        self.table[entry.hwid] = entry

    def get_port(self, hwid: HWID) -> Port:
        if hwid not in self.table:
            return None

        return self.table[hwid].port

    def get_hwids_by_port(self, port: Port) -> List[HWID]:
        return [x.hwid for x in self.table.values() if x.port == port]

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

    def delete_port(self, port: Port):
        for hwid in self.get_hwids_by_port(port):
            self.delete_hwid(hwid)


class Switch(Device):
    def __init__(
        self,
        name: Optional[str] = None,
        port_count: int = 4,
        cam_expire: int = 200,
        forward_capacity: Optional[int] = None,
    ):
        super().__init__(
            name=name,
            port_count=port_count,
            auto_process=True,
            process_rate=forward_capacity,
        )
        self.CAM = CAMTable(expiration=cam_expire)

    @property
    def forward_capacity(self):
        return self.process_rate

    def handle_connection_state_change(self, port: Port):
        super().handle_connection_state_change(port)
        self.CAM.delete_port(port)

    def run_jobs(self):
        self.CAM.expire()
        super().run_jobs()

    def process_packet(self, packet: Packet, port: Port):
        self.CAM.add_entry(packet.src, port)

        dst_port = (
            None
            if packet.dst == HWID.broadcast()
            else self.CAM.get_port(packet.dst)
        )
        if dst_port is None:
            # Unknown destination or destination is broadcast... flood!
            dst_ports = [x for x in self.ports if x != port]
        else:
            dst_ports = [dst_port]

        for dst_port in dst_ports:
            dst_port.send(packet)
