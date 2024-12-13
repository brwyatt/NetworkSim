import gzip
import json
import tkinter as tk
import tkinter.dnd as dnd
import traceback
from tkinter import filedialog

from networksim.serializer import deserialize
from networksim.simulation import Simulation
from networksim.ui.cable_shape import CableShape
from networksim.ui.errorwindow import ErrorWindow
from networksim.ui.objectlist import ObjectListPane
from networksim.ui.simcontrols import SimControlsPane
from networksim.ui.viewpane import ViewPane


class NetworkSimUI(tk.Frame):
    file_types_save = [
        ("NetworkSim JSON (Compressed)", "*.nsj.gz"),
        ("NetworkSim JSON", "*.nsj"),
    ]
    file_types_load = [("NetworkSim JSON types", ("*.nsj.gz", "*.nsj"))]

    def __init__(self, master=None):
        super().__init__(master=master)
        self.master.title("Network Sim")

        self.sim = Simulation()

        top = self.winfo_toplevel()
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.grid(sticky="NSEW")

        self.build()

    def step(self):
        self.sim.step()
        self.viewPort.step()
        self.controlsPane.step()

    def build_menubar(self):
        menubar = tk.Menu(self.winfo_toplevel())

        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Save...", command=self.save)
        filemenu.add_command(label="Load...", command=self.load)
        filemenu.add_separator()
        filemenu.add_command(label="Quit", command=self.quit)

        debugmenu = tk.Menu(menubar, tearoff=0)
        debugmenu.add_command(
            label="Print State (show())",
            command=self.sim.show,
        )

        menubar.add_cascade(label="File", menu=filemenu)
        menubar.add_cascade(label="Debug", menu=debugmenu)

        self.winfo_toplevel().config(menu=menubar)

    def build(self):
        self.build_menubar()

        self.viewPort = ViewPane(self, sim=self.sim)
        self.viewPort.grid(column=1, row=0, sticky="NSEW")

        self.objectList = ObjectListPane(
            self,
            add_handler=self.viewPort.add_device,
        )
        self.objectList.grid(column=0, row=0, rowspan=2, sticky="NSEW")

        self.controlsPane = SimControlsPane(self, sim=self.sim)
        self.controlsPane.grid(column=1, row=1, sticky="NSEW")

        self.update_size()

    def update_size(self):
        toplevel = self.winfo_toplevel()
        toplevel.update_idletasks()
        toplevel.update()
        reqwidth = toplevel.winfo_reqwidth()
        reqheight = toplevel.winfo_reqheight()
        toplevel.geometry(f"{reqwidth}x{reqheight}")

    def save(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=self.file_types_save[0][1],
            filetypes=[*self.file_types_save, ("All files", "*.*")],
        )

        if not file_path:
            return

        try:
            data = self.sim.serialize()
            data["ui_data"] = {
                "scale_factor": self.viewPort.scale_factor,
                "devices": {},
            }
            for device_shape in self.viewPort.devices:
                device_serial = getattr(device_shape.device, "__serial_id")
                coords = self.viewPort.coords(device_shape.rect)
                data["ui_data"]["devices"][device_serial] = {
                    "x": coords[0],
                    "y": coords[1],
                    "width": device_shape.width,
                    "height": device_shape.height,
                }
            serialized = json.dumps(data).encode()
            if file_path.endswith(".gz"):
                serialized = gzip.compress(serialized)
            with open(file_path, "wb") as file:
                file.write(serialized)
        except Exception as e:
            traceback.print_exc()
            ErrorWindow(
                self,
                text="\n".join(
                    [
                        "Error saving file!",
                        f"Path: {file_path}",
                        f"Error: {str(e)}",
                    ],
                ),
            )

    def load(self):
        file_path = filedialog.askopenfilename(
            filetypes=[*self.file_types_load, ("All files", "*.*")],
        )

        if not file_path:
            return

        try:
            with open(file_path, "rb") as file:
                data = file.read()

            if file_path.endswith(".gz"):
                data = gzip.decompress(data)
            data = json.loads(data.decode())
            ui_data = data.get("ui_data", {})
            data, context = deserialize(
                data["simulation"],
                context=data["context"],
            )

            self.sim = data
            self.build()

            self.viewPort.scale_factor = ui_data.get("scale_factor", 1.0)

            device_shapes_by_iface = {}
            for device in self.sim.devices:
                device_serial = getattr(device, "__serial_id")
                print(f"LOAD DEVICE: {device_serial}")
                device_shape_data = ui_data.get("devices", {}).get(
                    device_serial,
                    {},
                )
                device_shape = self.viewPort.add_device(
                    device,
                    x=device_shape_data.get("x"),
                    y=device_shape_data.get("y"),
                    width=device_shape_data.get("width"),
                    height=device_shape_data.get("height"),
                )
                for iface in device.ifaces:
                    device_shapes_by_iface[getattr(iface, "__serial_id")] = (
                        device_shape
                    )
            for cable in self.sim.cables:
                iface_a_serial = getattr(cable.a, "__serial_id")
                iface_b_serial = getattr(cable.b, "__serial_id")
                print(f"LOAD CABLE: {iface_a_serial} -> {iface_b_serial}")
                cable_shape = CableShape(
                    cable,
                    self.viewPort,
                    device_shapes_by_iface[iface_a_serial],
                    device_shapes_by_iface[iface_b_serial],
                )
                cable_shape.draw_packets()
                self.viewPort.cables.append(cable_shape)

        except Exception as e:
            traceback.print_exc()
            ErrorWindow(
                self,
                text="\n".join(
                    [
                        "Error loading file!",
                        f"Path: {file_path}",
                        f"Error: {str(e)}",
                    ],
                ),
            )


def start_ui():
    ui = NetworkSimUI()
    ui.mainloop()
