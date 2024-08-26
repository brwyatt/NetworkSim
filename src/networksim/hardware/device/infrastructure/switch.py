from typing import List

from networksim.hardware.device import Device
from networksim.hardware.port import Port
from networksim.hwid import HWID


class CAMEntry:
    def __init__(self, hwid: HWID, port: Port, expiration: int = 100):
        self.hwid = hwid
        self.port = port
        self.expiration = expiration

    def __eq__(self, other):
        return (self.hwid == other.hwid) and (self.port == other.port)


class CAMTable:
    def __init__(self, expiration: int = 100):
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
    def __init__(self, port_count: int = 4, cam_expire: int = 100):
        super().__init__(port_count=port_count)
        self.CAM = CAMTable(expiration=cam_expire)

    def step(self):
        self.CAM.expire()
        for port in self.ports:
            if self.connection_states[port] != port.connected:
                # Connection state has changed, flush port from CAM
                self.connection_states[port] = port.connected
                self.CAM.delete_port(port)

            packet = port.receive()
            if packet is not None:
                self.CAM.add_entry(packet.src, port)

                dst_port = self.CAM.get_port(packet.dst)
                if dst_port is None:
                    # We don't know the destination... flood!
                    dst_ports = [x for x in self.ports if x != port]
                else:
                    dst_ports = [dst_port]

                for dst_port in dst_ports:
                    dst_port.send(packet)

    def __getitem__(self, index):
        return self.ports[index]
