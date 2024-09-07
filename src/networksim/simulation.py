from networksim.hardware.cable import Cable
from networksim.hardware.device import Device
from networksim.hardware.device.infrastructure.switch import Switch
from networksim.hardware.device.ip.ipdevice import IPDevice
from networksim.hardware.port import Port


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
            for x in range(0, len(device.ports)):
                print(
                    f"   * Port[{x}]"
                    + (
                        f" ({device[x].hwid})"
                        if not isinstance(device, Switch)
                        else ""
                    )
                    + f": {len(device[x].inbound_queue)} | {len(device[x].outbound_queue)}",
                )
                if isinstance(device, IPDevice):
                    for bind in device.ip.bound_ips.get_binds(port=device[x]):
                        print(f"     * {bind.addr}/{bind.network.match_bits}")

    def print_cables(self):
        print("CABLES (a->b | b->a):")
        for cable in self.cables:
            port_a = None
            port_b = None

            for device in self.devices:
                try:
                    port_a = f"{device.name}[{device.port_id(cable.a)}]"
                except ValueError:
                    pass
                try:
                    port_b = f"{device.name}[{device.port_id(cable.b)}]"
                except ValueError:
                    pass
                if port_a is not None and port_b is not None:
                    break

            if port_a is None:
                port_a = str(cable.a.hwid)
            if port_b is None:
                port_b = str(cable.b.hwid)

            print(
                f" * {port_a}/{port_b}: {[str(x) for x in cable.ab_transit]} | {[str(x) for x in cable.ba_transit]}",
            )

    def print_cam_tables(self):
        print("CAM TABLES:")
        for device in self.devices:
            if not isinstance(device, Switch):
                continue
            print(f" * {device.name}")
            for x in range(0, len(device.ports)):
                print(
                    f"   * Port[{x}]: {[str(x) for x in device.CAM.get_hwids_by_port(device[x])]}",
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
        a_port = None
        for port in a.ports:
            a_port = port
            if not port.connected:
                break

        b_port = None
        for port in b.ports:
            b_port = port
            if not port.connected:
                break

        cable = Cable(a_port, b_port, length, max_bandwidth=bandwidth)

        self.add_device(a)
        self.add_device(b)
        self.add_cable(cable)
