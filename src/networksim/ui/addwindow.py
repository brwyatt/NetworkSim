import tkinter as tk
import traceback
from typing import List
from typing import Optional
from typing import Type

from networksim.hardware.device import Device
from networksim.ui.errorwindow import ErrorWindow
from networksim.ui.object_builder_frames import ObjectBuilderFrame


class AddWindow(tk.Toplevel):
    def __init__(
        self,
        master=None,
        *args,
        cls: Type,
        callback: callable,
        ignore_list: Optional[List[str]] = None,
    ):
        super().__init__(master=master)

        self.cls = cls
        self.callback = callback
        self.ignore_list = ignore_list

        self.title(f"Adding {cls.__name__}")
        self.transient(master.winfo_toplevel())
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Leaving first row vacant for now (maybe add label later?)

        self.fields_frame = ObjectBuilderFrame(
            self,
            cls=self.cls,
            ignore_list=self.ignore_list,
        )
        self.fields_frame.grid(column=0, row=1, columnspan=2, sticky="NSEW")

        self.okay = tk.Button(self, text="OK", command=self.submit)
        self.okay.grid(column=0, row=2, sticky="SE")
        self.cancel = tk.Button(self, text="Cancel", command=self.close)
        self.cancel.grid(column=1, row=2, sticky="SW")

        self.resizable(False, False)

        self.wait_visibility()
        self.grab_set()

    def submit(self):
        try:
            obj = self.fields_frame.get()
        except Exception as e:
            traceback.print_exc()
            ErrorWindow(
                master=self,
                text=f"Data error, invalid field input: {e}",
            )
        else:
            self.callback(obj)
            self.close()

    def close(self):
        # re-activate parent window
        self.grab_release()
        # just in case
        self.master.winfo_toplevel().deiconify()
        self.destroy()
