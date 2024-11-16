import inspect
import tkinter as tk
from dataclasses import dataclass
from dataclasses import fields
from dataclasses import make_dataclass
from enum import Enum
from typing import Dict
from typing import List
from typing import Optional
from typing import TYPE_CHECKING

import pkg_resources
from networksim.hardware.device import Device
from networksim.hardware.interface import Interface
from networksim.ipaddr import IPAddr
from networksim.ipaddr import IPNetwork
from networksim.packet import Packet
from networksim.packet.ethernet import EthernetPacket
from networksim.ui.addwindow import AddWindow
from networksim.ui.logviewwindow import LogViewWindow
from networksim.ui.packet_menu import create_packet_menu

if TYPE_CHECKING:
    from networksim.ui.viewpane import ViewPane


@dataclass
class ip_bind:
    addr: IPAddr
    network: IPNetwork


class DeviceShape:
    def __init__(
        self,
        device: Device,
        canvas: "ViewPane",
        x: int,
        y: int,
        width: int = 50,
        height: int = 50,
        label: Optional[str] = None,
    ):
        self.device = device
        self.canvas = canvas
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.update_handlers = []

        font_size = 10

        self.bgrect = canvas.create_rectangle(
            x,
            y,
            x + width,
            y + height + font_size + 2,
            width=0,
        )
        self.rect = canvas.create_rectangle(
            x,
            y,
            x + width,
            y + height,
            fill="blue",
        )
        self.text = canvas.create_text(
            x + (width / 2),
            y + height + (font_size / 2) + 2,
            font=("Helvetica", font_size, "bold"),
            text=label if label is not None else device.name,
        )

        self.shapes = (self.bgrect, self.rect, self.text)
        for shape in self.shapes:
            canvas.tag_bind(shape, "<ButtonPress-1>", self.left_click)
            canvas.tag_bind(shape, "<B1-Motion>", self.drag)
            canvas.tag_bind(shape, "<ButtonPress-3>", self.right_click)

    def send_updates(self):
        for handler in self.update_handlers:
            handler()

    def add_update_handler(self, handler):
        if handler not in self.update_handlers:
            self.update_handlers.append(handler)

    def del_update_handler(self, handler):
        if handler in self.update_handlers:
            self.update_handlers.remove(handler)

    def get_midpoint(self):
        x1, y1, x2, y2 = self.canvas.coords(self.rect)
        return (x1 + ((x2 - x1) / 2)), (y1 + ((y2 - y1) / 2))

    def delete(self):
        for shape in self.shapes:
            self.canvas.delete(shape)

    def get_add_application_handler(self, entry_point):
        def handler():
            self.device.add_application(entry_point.load(), entry_point.name)

        return handler

    def create_add_application_menu(self, master, handler_generator):
        app_menu = tk.Menu(master, tearoff=False)

        for entry_point in pkg_resources.iter_entry_points(
            "networksim_applications",
        ):
            if entry_point.name in self.device.applications:
                continue
            app_menu.add_command(
                label=entry_point.name,
                command=handler_generator(entry_point),
            )

        return app_menu

    def create_iface_connect_menu(self, master, handler_generator):
        iface_menu = tk.Menu(master, tearoff=False)
        iface_num = -1
        for iface in self.device.ifaces:
            iface_num += 1
            if iface.connected:
                continue
            iface_menu.add_command(
                label=f"{iface_num} - ({str(iface.hwid)})",
                command=handler_generator(iface),
            )

        return iface_menu

    def get_add_bind_handler(self, iface: Interface):
        def handler():
            AddWindow(
                master=self.canvas.winfo_toplevel(),
                cls=ip_bind,
                callback=lambda bind: self.device.ip.bind(
                    addr=bind.addr,
                    network=bind.network,
                    iface=iface,
                ),
            )

        return handler

    def get_delete_bind_handler(self, addr: IPAddr, iface: Interface):
        def handler():
            self.device.ip.unbind(addr=addr, iface=iface)

        return handler

    def get_garp_handler(self, addr: IPAddr, iface: Interface):
        def handler():
            self.device.ip.send_garp(addr=addr, iface=iface)

        return handler

    def get_create_send_packet(self, iface: Interface):
        def handler():
            return self.create_send_packet(iface)

        return handler

    def get_inbound_flush_handler(self, iface: Interface):
        def handler():
            return iface.inbound_flush()

        return handler

    def get_outbound_flush_handler(self, iface: Interface):
        def handler():
            return iface.outbound_flush()

        return handler

    def copy_text(self, text: str):
        self.canvas.clipboard_clear()
        self.canvas.clipboard_append(text)

    def get_copy_handler(self, text: str):
        def handler():
            self.copy_text(str(text))

        return handler

    def create_ifaces_menu(self, master):
        ifaces_menu = tk.Menu(master, tearoff=False)

        iface_num = -1
        for iface in self.device.ifaces:
            iface_num += 1

            iface_menu = tk.Menu(ifaces_menu, tearoff=False)

            if not iface.connected:
                iface_menu.add_command(
                    label="Connect",
                    command=self.get_start_connect_handler(iface),
                )
            else:
                binds_menu = tk.Menu(iface_menu, tearoff=False)
                if hasattr(self.device, "ip"):
                    for bind in self.device.ip.bound_ips.get_binds(
                        iface=iface,
                    ):
                        bind_menu = tk.Menu(binds_menu, tearoff=False)
                        bind_menu.add_command(
                            label="Copy IPAddr",
                            command=self.get_copy_handler(bind.addr),
                        )
                        bind_menu.add_command(
                            label="Remove Bind",
                            command=self.get_delete_bind_handler(
                                addr=bind.addr,
                                iface=iface,
                            ),
                        )
                        bind_menu.add_command(
                            label="Send Gratuitous ARP",
                            command=self.get_garp_handler(
                                addr=bind.addr,
                                iface=iface,
                            ),
                        )
                        binds_menu.add_cascade(
                            label=f"{bind.addr}/{bind.network.match_bits}",
                            menu=bind_menu,
                        )
                    binds_menu.add_command(
                        label="Add Bind",
                        command=self.get_add_bind_handler(iface),
                    )
                    iface_menu.add_cascade(
                        label="IP Binds",
                        menu=binds_menu,
                    )
                iface_menu.add_command(
                    label="Copy HWID",
                    command=self.get_copy_handler(iface.hwid),
                )
                iface_menu.add_command(
                    label="Send Packet",
                    command=self.get_create_send_packet(iface),
                )
                # Buffer menus
                send_queue_menu = tk.Menu(iface_menu, tearoff=0)
                send_queue_menu.add_command(
                    label="Flush Queue",
                    command=self.get_outbound_flush_handler(iface),
                )
                packet_count = -1
                for packet in iface.outbound_queue:
                    packet_count += 1
                    send_queue_menu.add_cascade(
                        label=f"[{packet_count}] {type(packet).__name__}",
                        menu=create_packet_menu(send_queue_menu, packet),
                    )
                iface_menu.add_cascade(
                    label=f"Send Queue ({len(iface.outbound_queue)})",
                    menu=send_queue_menu,
                )
                rec_queue_menu = tk.Menu(iface_menu, tearoff=0)
                rec_queue_menu.add_command(
                    label="Flush Queue",
                    command=self.get_inbound_flush_handler(iface),
                )
                packet_count = -1
                for packet in iface.inbound_queue:
                    packet_count += 1
                    rec_queue_menu.add_cascade(
                        label=f"[{packet_count}] {type(packet).__name__}",
                        menu=create_packet_menu(rec_queue_menu, packet),
                    )
                iface_menu.add_cascade(
                    label=f"Receive Queue ({len(iface.inbound_queue)})",
                    menu=rec_queue_menu,
                )
            ifaces_menu.add_cascade(
                label=f"{iface_num} - ({str(iface.hwid)})",
                menu=iface_menu,
            )

        return ifaces_menu

    def get_dataclass_for_function(
        self,
        func: callable,
        name: Optional[str] = None,
        ignore: Optional[List[str]] = None,
        overrides: Optional[Dict[str, type]] = None,
    ):
        name = name if name is not None else f"{func.__name__}_data"
        overrides = overrides if overrides is not None else {}
        ignore = ["args", "kwargs"] + (ignore if ignore is not None else [])
        sig = inspect.signature(func)
        fields = []
        for field in sig.parameters.values():
            if field.name in ignore:
                continue
            annotation = field.annotation
            if field.name in overrides:
                annotation = overrides[field.name]
            if field.default == inspect.Parameter.empty:
                fields.append((field.name, annotation))
            else:
                fields.append((field.name, annotation, field.default))
        return make_dataclass(name, fields)

    def get_start_application_handler(self, name, application):
        datacls = self.get_dataclass_for_function(
            application,
            name=name,
            ignore=["device"],
        )

        def callback(data):
            self.device.start_application(name, **data.__dict__)

        def handler():
            if len(fields(datacls)) == 0:
                callback(datacls())
            else:
                AddWindow(
                    master=self.canvas.winfo_toplevel(),
                    cls=datacls,
                    callback=callback,
                )

        return handler

    def create_start_application_menu(self, master):
        app_menu = tk.Menu(master, tearoff=False)

        for name, application in self.device.applications.items():
            app_menu.add_command(
                label=name,
                command=self.get_start_application_handler(name, application),
            )

        return app_menu

    def get_stop_application_handler(self, id):
        def handler():
            self.device.stop_application(id)

        return handler

    def get_proc_log_handler(self, application):
        def handler():
            LogViewWindow(
                self.canvas.winfo_toplevel(),
                title=f"Application logs for {application.__class__.__name__}",
                log=application.log,
            )

        return handler

    def create_process_menu(self, master):
        proc_list_menu = tk.Menu(master, tearoff=False)

        for id, application in sorted(
            self.device.process_list.items(),
            key=lambda x: x[0],
        ):
            proc_menu = tk.Menu(proc_list_menu, tearoff=False)
            proc_menu.add_command(
                label="Stop process",
                command=self.get_stop_application_handler(id),
            )
            proc_menu.add_command(
                label="View process logs",
                command=self.get_proc_log_handler(application),
            )
            proc_list_menu.add_cascade(
                label=f"[{id}] {application.__class__.__name__}",
                menu=proc_menu,
            )

        return proc_list_menu

    def raise_shapes(self):
        for shape in self.shapes:
            self.canvas.tag_raise(shape)

    def get_delete_route_handler(self, bind):
        def handler():
            self.device.ip.routes.del_routes(
                bind.network,
                bind.iface,
                bind.via,
                bind.src,
            )

        return handler

    @property
    def iface_enum(self):
        return Enum("iface", {str(iface.hwid): iface for iface in self.device.ifaces})  # type: ignore

    def add_route(self):
        _route_bind = self.get_dataclass_for_function(
            self.device.ip.routes.add_route,
            overrides={
                "iface": self.iface_enum,
            },
        )

        AddWindow(
            master=self.canvas.winfo_toplevel(),
            cls=_route_bind,
            callback=lambda bind: self.device.ip.routes.add_route(
                **{**bind.__dict__, "iface": bind.iface.value},
            ),
        )

    def get_delete_ip_handler(self, bind):
        def handler():
            self.device.ip.bound_ips.del_binds(
                bind.addr,
                bind.network,
                bind.iface,
            )

        return handler

    def add_ip(self):
        _ip_bind = self.get_dataclass_for_function(
            self.device.ip.bind,
            overrides={
                "iface": self.iface_enum,
            },
        )

        AddWindow(
            master=self.canvas.winfo_toplevel(),
            cls=_ip_bind,
            callback=lambda bind: self.device.ip.bind(
                **{**bind.__dict__, "iface": bind.iface.value},
            ),
        )

    def create_ip_menu(self, master):
        ip_menu = tk.Menu(master, tearoff=False)

        ip_binds_menu = tk.Menu(ip_menu, tearoff=False)
        for bind in self.device.ip.bound_ips.get_binds():
            bind_menu = tk.Menu(ip_binds_menu, tearoff=False)
            bind_menu.add_command(
                label="Delete IP",
                command=self.get_delete_ip_handler(bind),
            )
            ip_binds_menu.add_cascade(
                label=f"{bind.addr}/{bind.network.match_bits}",
                menu=bind_menu,
            )
        ip_binds_menu.add_command(label="Add IP", command=self.add_ip)
        ip_menu.add_cascade(label="Addresses", menu=ip_binds_menu)

        route_binds_menu = tk.Menu(ip_menu, tearoff=False)
        for bind in self.device.ip.routes.routes:
            bind_menu = tk.Menu(route_binds_menu, tearoff=False)
            if bind.via:
                bind_menu.add_command(label=f"via: {bind.via}")
            if bind.src:
                bind_menu.add_command(label=f"src: {bind.src}")
            bind_menu.add_command(label=f"dev: {bind.iface.hwid}")
            bind_menu.add_command(
                label="Delete Route",
                command=self.get_delete_route_handler(bind),
            )
            route_binds_menu.add_cascade(
                label=f"{bind.network}",
                menu=bind_menu,
            )
        route_binds_menu.add_command(label="Add Route", command=self.add_route)
        ip_menu.add_cascade(label="Routes", menu=route_binds_menu)

        return ip_menu

    def create_menu(self, event):
        menu = tk.Menu(self.canvas, tearoff=0)

        menu.add_command(
            label="Delete",
            command=lambda: self.canvas.delete_device(self),
        )

        iface_menu = self.create_ifaces_menu(menu)
        menu.add_cascade(label="Interfaces", menu=iface_menu)

        if hasattr(self.device, "ip"):
            ip_menu = self.create_ip_menu(menu)
            menu.add_cascade(label="IP", menu=ip_menu)

        add_app_menu = self.create_add_application_menu(
            menu,
            self.get_add_application_handler,
        )
        menu.add_cascade(label="Add Application", menu=add_app_menu)

        if len(self.device.applications) > 0:
            start_app_menu = self.create_start_application_menu(menu)
            menu.add_cascade(label="Start Application", menu=start_app_menu)

        if len(self.device.process_list) > 0:
            proc_list_menu = self.create_process_menu(menu)
            menu.add_cascade(label="Processes", menu=proc_list_menu)

        menu.post(event.x_root, event.y_root)
        self.canvas.menu = menu

        return menu

    def create_send_packet(self, iface: Interface):
        AddWindow(
            master=self.canvas.winfo_toplevel(),
            cls=EthernetPacket,
            callback=iface.send,
        )

    def right_click(self, event):
        self.canvas.last_event = event.serial
        self.canvas.remove_menu(event)

        self.raise_shapes()

        self.create_menu(event)

    def get_start_connect_handler(self, iface):
        def handler():
            self.canvas.start_connect(self, iface)

        return handler

    def get_end_connect_handler(self, iface):
        def handler():
            self.canvas.select_connect_end(self, iface)

        return handler

    def left_click(self, event):
        self.raise_shapes()

        if (
            self.canvas.connect_start is not None
            and self.canvas.connect_start not in (self.device.ifaces)
        ):
            self.canvas.remove_menu(event)
            self.canvas.last_event = event.serial
            menu = self.create_iface_connect_menu(
                self.canvas,
                self.get_end_connect_handler,
            )
            menu.post(event.x_root, event.y_root)
            self.canvas.menu = menu

        self.start_drag(event)

    def start_drag(self, event):
        self.canvas.last_event = event.serial

        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.canvas.drag_start_x = None
        self.canvas.drag_start_y = None

    def drag(self, event):
        if self.canvas.connect_start is not None:
            return

        self.canvas.last_event = event.serial
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y

        for shape in self.shapes:
            self.canvas.move(shape, dx, dy)

        self.send_updates()

        self.drag_start_x = event.x
        self.drag_start_y = event.y
