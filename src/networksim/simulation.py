from networksim.hardware.cable import Cable
from networksim.hardware.device import Device
from networksim.hardware.device.infrastructure.switch import Switch
from networksim.hardware.device.ip.ipdevice import IPDevice
from networksim.hardware.interface import Interface


class Simulation:
    def __init__(self):
        self.cables = []
        self.devices = []

    def step(self, steps: int = 1):
        for _ in range(0, steps):
            for x in self.cables + self.devices:
                x.step()

    def print_devices(self):
        print("DEVICES (queue in | queue out):")
        for device in self.devices:
            print(f" * {device.name}:")
            for x in range(0, len(device.ifaces)):
                print(
                    f"   * Iface[{x}]"
                    + (
                        f" ({device[x].hwid})"
                        if not isinstance(device, Switch)
                        else ""
                    )
                    + f": {len(device[x].inbound_queue)} | {len(device[x].outbound_queue)}",
                )
                if isinstance(device, IPDevice):
                    for bind in device.ip.bound_ips.get_binds(iface=device[x]):
                        print(f"     * {bind.addr}/{bind.network.match_bits}")

    def print_cables(self):
        print("CABLES (a->b | b->a):")
        for cable in self.cables:
            iface_a = None
            iface_b = None

            for device in self.devices:
                try:
                    iface_a = f"{device.name}[{device.iface_id(cable.a)}]"
                except ValueError:
                    pass
                try:
                    iface_b = f"{device.name}[{device.iface_id(cable.b)}]"
                except ValueError:
                    pass
                if iface_a is not None and iface_b is not None:
                    break

            if iface_a is None:
                iface_a = "Unconnected"
                if cable.a is not None:
                    iface_a = str(cable.a.hwid)
            if iface_b is None:
                iface_b = "Unconnected"
                if cable.b is not None:
                    iface_b = str(cable.b.hwid)

            print(
                f" * {iface_a}/{iface_b}: {[str(x) for x in cable.ab_transit]} | {[str(x) for x in cable.ba_transit]}",
            )

    def print_cam_tables(self):
        print("CAM TABLES:")
        for device in self.devices:
            if not isinstance(device, Switch):
                continue
            print(f" * {device.name}")
            for x in range(0, len(device.ifaces)):
                print(
                    f"   * Iface[{x}]: {[str(x) for x in device.CAM.get_hwids_by_iface(device[x])]}",
                )

    def print_arp_tables(self):
        print("ARP TABLES:")
        for device in self.devices:
            if not isinstance(device, IPDevice):
                continue
            print(f" * {device.name}")
            for x, y in device.ip.addr_table.table.items():
                print(f"   * {x}: {y.hwid}")

    def print_route_tables(self):
        print("ROUTE TABLES:")
        for device in self.devices:
            if not isinstance(device, IPDevice):
                continue
            print(f" * {device.name}")
            for route in device.ip.routes.routes:
                print(f"   * {route}")

    def show(self):
        self.print_devices()
        self.print_cables()
        self.print_cam_tables()
        self.print_arp_tables()
        self.print_route_tables()

    def add_device(self, device: Device):
        if device not in self.devices:
            self.devices.append(device)

    def delete_device(self, device: Device):
        # disconnect from cables from device
        for cable in self.cables:
            if cable.a in device.ifaces:
                cable.a = None
            if cable.b in device.ifaces:
                cable.b = None

        # remove device from simulation
        if device in self.devices:
            self.devices.remove(device)

    def add_cable(self, cable: Cable):
        if cable not in self.cables:
            self.cables.append(cable)

    def connect_devices(
        self,
        a: Device,
        b: Device,
        length: int = 3,
        bandwidth: int = 1,
    ):
        a_iface = None
        for iface in a.ifaces:
            a_iface = iface
            if not iface.connected:
                break

        b_iface = None
        for iface in b.ifaces:
            b_iface = iface
            if not iface.connected:
                break

        cable = Cable(a_iface, b_iface, length, max_bandwidth=bandwidth)

        self.add_device(a)
        self.add_device(b)
        self.add_cable(cable)
