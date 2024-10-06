import tkinter as tk
from collections import defaultdict

import pkg_resources
from networksim.ui.toggleframe import ToggleFrame


def device_tree():
    return defaultdict(device_tree)


class ObjectListPane(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master=master)

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
                widget = ToggleFrame(master=parent, title=name)
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
            print(f"NAME: {name}, CLS: {cls.__module__}.{cls.__name__}")

        return handler

    def build(self):
        self.root_toggle_frame = ToggleFrame(
            master=self,
            title="Devices",
            show_default=True,
        )
        self.root_toggle_frame.pack(fill="x")
        self.create_widgets_from_device_types(self.root_toggle_frame.contents)
