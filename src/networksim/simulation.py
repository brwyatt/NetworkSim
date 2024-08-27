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
                    f"   * Port {x}: {device.ports[x].inbound_queue.qsize()} | {device.ports[x].outbound_queue.qsize()}",
                )

        print("CABLES (a->b | b->a):")
        for cable in self.cables:
            print(
                f" * {cable.a.hwid}/{cable.b.hwid}: {[str(x) for x in cable.ab_transit]} | {[str(x) for x in cable.ba_transit]}",
            )

        print("CAM TABLES:")
        for device in self.devices:
            if not isinstance(device, Switch):
                continue
            print(f" * {device.name}")
            for x in range(0, len(device.ports)):
                print(
                    f"   * Port {x}: {[str(x) for x in device.CAM.get_hwids_by_port(device.ports[x])]}",
                )

    def add_device(self, device: Device):
        if device not in self.devices:
            self.devices.append(device)

    def add_cable(self, cable: Cable):
        if cable not in self.cables:
            self.cables.append(cable)

    def connect_devices(self, a: Device, b: Device):
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

        cable = Cable(a_port, b_port)

        self.add_device(a)
        self.add_device(b)
        self.add_cable(cable)
