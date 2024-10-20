import tkinter as tk
import tkinter.dnd as dnd

from networksim.simulation import Simulation
from networksim.ui.objectlist import ObjectListPane
from networksim.ui.simcontrols import SimControlsPane
from networksim.ui.viewpane import ViewPane


class NetworkSimUI(tk.Frame):
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

    def build(self):
        self.viewPort = ViewPane(self, sim=self.sim)
        self.viewPort.grid(column=1, row=0, sticky="NSEW")

        self.objectList = ObjectListPane(
            self,
            add_handler=self.viewPort.add_device,
        )
        self.objectList.grid(column=0, row=0, rowspan=2, sticky="NSEW")

        self.controlsPane = SimControlsPane(self, sim=self.sim)
        self.controlsPane.grid(column=1, row=1, sticky="NSEW")


def start_ui():
    ui = NetworkSimUI()
    ui.mainloop()
