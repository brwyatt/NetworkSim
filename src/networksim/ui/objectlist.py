import inspect
import tkinter as tk
from collections import defaultdict

import pkg_resources
from networksim.ui.addwindow import AddWindow
from networksim.ui.toggleframe import ToggleFrame


def device_tree():
    return defaultdict(device_tree)


class ObjectListPane(tk.Frame):
    def __init__(self, master=None, *args, add_handler):
        super().__init__(master=master)

        self.add_to_view = add_handler

        self.device_types = device_tree()
        for entry_point in pkg_resources.iter_entry_points(
            "networksim_device_types",
        ):
            self.add_device_type(entry_point.name, entry_point.load())

        self.build()

    def add_device_type(self, path, cls):
        path = path.split(".")
        name = path[-1]
        path = path[:-1]

        temp = self.device_types
        for level in path:
            temp = temp[level]

        temp[name] = cls

    def create_widgets_from_device_types(self, parent=None, device_types=None):
        if parent is None:
            parent = self
        if device_types is None:
            device_types = self.device_types

        for name, value in device_types.items():
            widget = None
            if isinstance(value, (dict, defaultdict)):
                widget = ToggleFrame(
                    master=parent,
                    title=name,
                    toggle_update=self.update_canvas_size,
                )
                self.create_widgets_from_device_types(widget.contents, value)
            else:
                widget = tk.Button(
                    parent,
                    text=name,
                    command=self.get_button_handler(name, value),
                )
            widget.pack(fill="x")

    def get_button_handler(self, name, cls):
        def handler():
            AddWindow(self, device_cls=cls, add_handler=self.add_to_view)

        return handler

    def build(self):
        self.canvas = tk.Canvas(self)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar = tk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview,
        )

        self.scrollbar.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all"),
            ),
        )

        self.inner_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.root_toggle_frame = ToggleFrame(
            master=self.inner_frame,
            title="Devices",
            show_default=True,
            toggle_update=self.update_canvas_size,
        )

        self.root_toggle_frame.pack(fill="x")
        self.create_widgets_from_device_types(self.root_toggle_frame.contents)

        self.update_canvas_size()

    def update_canvas_size(self):
        self.canvas.update_idletasks()
        self.canvas.config(
            width=self.inner_frame.winfo_reqwidth(),
        )
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
