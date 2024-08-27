from networksim.hardware.cable import Cable
from networksim.hardware.device import Device
from networksim.hardware.device.infrastructure.switch import Switch
from networksim.hardware.port import Port


class Simulation:
    def __init__(self):
        self.cables = []
        self.devices = []

    def step(self):
        for x in self.cables + self.devices:
            x.step()

    def show(self):
        print("DEVICES (queue in | queue out):")
        for device in self.devices:
            print(f" * {device.name}:")
            for x in range(0, len(device.ports)):
                print(
                    f"   * Port {x}: {device[x].inbound_queue.qsize()} | {device[x].outbound_queue.qsize()}",
                )

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

        print("CAM TABLES:")
        for device in self.devices:
            if not isinstance(device, Switch):
                continue
            print(f" * {device.name}")
            for x in range(0, len(device.ports)):
                print(
                    f"   * Port {x}: {[str(x) for x in device.CAM.get_hwids_by_port(device[x])]}",
                )

    def add_device(self, device: Device):
        if device not in self.devices:
            self.devices.append(device)

    def add_cable(self, cable: Cable):
        if cable not in self.cables:
            self.cables.append(cable)

    def connect_devices(self, a: Device, b: Device, length: int = 3):
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

        cable = Cable(a_port, b_port, length)

        self.add_device(a)
        self.add_device(b)
        self.add_cable(cable)
