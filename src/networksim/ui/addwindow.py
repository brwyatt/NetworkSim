import tkinter as tk
from typing import Type

from networksim.hardware.device import Device
from networksim.ui.object_builder_frames import ObjectBuilderFrame


class AddWindow(tk.Toplevel):
    def __init__(
        self,
        master=None,
        *args,
        device_cls: Type[Device],
        add_handler: callable,
    ):
        super().__init__(master=master)

        self.device_cls = device_cls
        self.add_to_view = add_handler

        self.title(f"Adding {device_cls.__name__}")
        self.transient(master.winfo_toplevel())
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Leaving first row vacant for now (maybe add label later?)

        self.fields_frame = ObjectBuilderFrame(self, cls=self.device_cls)
        self.fields_frame.grid(column=0, row=1, columnspan=2, sticky="NSEW")

        self.okay = tk.Button(self, text="OK", command=self.submit)
        self.okay.grid(column=0, row=2, sticky="SE")
        self.cancel = tk.Button(self, text="Cancel", command=self.close)
        self.cancel.grid(column=1, row=2, sticky="SW")

        self.grab_set()

    def submit(self):
        self.add_to_view(self.fields_frame.get())
        self.close()

    def close(self):
        # re-activate parent window
        self.grab_release()
        # just in case
        self.master.winfo_toplevel().deiconify()
        self.destroy()
