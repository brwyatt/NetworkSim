import logging
from collections import defaultdict
from typing import Dict
from typing import List
from typing import Optional
from typing import Type
from typing import TYPE_CHECKING

from networksim.hardware.interface import Interface
from networksim.helpers import randbytes
from networksim.hwid import HWID
from networksim.packet import Packet

if TYPE_CHECKING:
    from networksim.application import Application


logger = logging.getLogger(__name__)


class Device:
    default_iface_count = 1

    def __init__(
        self,
        name: Optional[str] = None,
        auto_process: bool = False,
        ifaces: Optional[List[Interface]] = None,
        process_rate: Optional[int] = None,
    ):
        self.base_MAC = randbytes(5)
        if name is None:
            name = f"{type(self).__name__}-{self.base_MAC.hex()}"
        self.name = name
        self.ifaces = []
        self.connection_states = defaultdict(lambda: False)
        self.auto_process = auto_process
        self.time = 0

        if ifaces is None:
            for x in range(1, self.default_iface_count + 1):
                self.add_iface(HWID(self.base_MAC + int.to_bytes(x, 1, "big")))
        else:
            self.ifaces.extend(ifaces)

        # By default, be able to process combined full (max) line-rate
        self.process_rate = (
            process_rate
            if process_rate is not None
            else sum([x.max_bandwidth for x in self.ifaces])
        )

        self.applications: Dict[str, Type["Application"]] = {}  # noqa: F821
        self.process_list: Dict[int, "Application"] = {}  # noqa: F821
        self.next_pid = 1

    def add_iface(self, hwid: Optional[HWID] = None):
        self.ifaces.append(Interface(hwid))

    def handle_connection_state_change(self, iface: Interface):
        pass

    def check_connection_state_changes(self):
        for iface in self.ifaces:
            if self.connection_states[iface] != iface.connected:
                # Connection state has changed!
                self.connection_states[iface] = iface.connected
                self.handle_connection_state_change(iface)

    def add_application(
        self,
        application: Type["Application"],  # noqa: F821
        name: Optional[str] = None,
    ):
        if name is None:
            name = application.__name__

        if name in self.applications:
            raise KeyError("Application already registered")

        self.applications[name] = application

    def start_application(self, name: str, *args, **kwargs) -> int:
        proc = self.applications[name](self, *args, **kwargs)
        proc.start()
        self.process_list[self.next_pid] = proc
        self.next_pid += 1

        return self.next_pid - 1

    def stop_application(self, pid: int):
        try:
            self.process_list[pid].stop()
            del self.process_list[pid]
        except KeyError:
            pass

    def process_payload(
        self,
        payload,
        src: Optional[HWID] = None,
        dst: Optional[HWID] = None,
        iface: Optional[Interface] = None,
    ):
        logger.info(payload)

    def process_packet(self, packet: Packet, iface: Interface):
        if packet.dst not in [iface.hwid, HWID.broadcast()]:
            logger.info(
                f"Ignoring packet from {packet.src} for {packet.dst} (not us!)",
            )
            return
        logger.info(
            "Received "
            + ("broadcast" if packet.dst == HWID.broadcast() else "unicast")
            + f" packet from {packet.src}",
        )
        self.process_payload(
            packet.payload,
            packet.src,
            packet.dst,
            iface,
        )

    def process_inputs(self):
        processed = 0
        has_processed = True
        while processed < self.process_rate and has_processed:
            has_processed = False
            for iface in self.ifaces:
                if processed >= self.process_rate:
                    break
                packet = iface.receive()
                if packet is not None:
                    self.process_packet(packet, iface)

                    has_processed = True
                    processed += 1

    def run_jobs(self):
        pass

    def run_applications(self):
        for application in self.process_list.values():
            application.step()

    def step(self):
        self.time += 1
        self.check_connection_state_changes()
        self.run_jobs()
        self.run_applications()
        if self.auto_process:
            self.process_inputs()

    def __getitem__(self, index):
        return self.ifaces[index]

    def iface_id(self, iface: Interface):
        return self.ifaces.index(iface)
