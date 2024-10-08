import inspect
import tkinter as tk
from collections import defaultdict

import pkg_resources
from networksim.ui.addwindow import AddWindow
from networksim.ui.toggleframe import ToggleFrame


def device_tree():
    return defaultdict(device_tree)


class ObjectListPane(tk.Frame):
    header_bg = "navy"
    header_fg = "lightgrey"
    header_active_bg = "blue"
    header_active_fg = "lightgrey"

    item_bg = "darkgreen"
    item_fg = "lightgrey"
    item_active_bg = "green"
    item_active_fg = "lightgrey"

    def __init__(self, master=None, *args, add_handler, hide_scrollbar=False):
        super().__init__(master=master)

        self.add_to_view = add_handler
        self.hide_scrollbar = hide_scrollbar

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
                    bg=self.header_bg,
                    fg=self.header_fg,
                    activebackground=self.header_active_bg,
                    activeforeground=self.header_active_fg,
                )
                self.create_widgets_from_device_types(widget.contents, value)
            else:
                widget = tk.Button(
                    parent,
                    text=name,
                    command=self.get_button_handler(name, value),
                    bg=self.item_bg,
                    fg=self.item_fg,
                    activebackground=self.item_active_bg,
                    activeforeground=self.item_active_fg,
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

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind(
            "<Configure>",
            self.update_canvas_size,
        )

        if not self.hide_scrollbar:
            self.scrollbar.pack(side="right", fill="y")

        self.inner_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.root_toggle_frame = ToggleFrame(
            master=self.inner_frame,
            title="Devices",
            show_default=True,
            toggle_update=self.update_canvas_size,
            bg=self.header_bg,
            fg=self.header_fg,
            activebackground=self.header_active_bg,
            activeforeground=self.header_active_fg,
        )

        self.root_toggle_frame.pack(fill="x")
        self.create_widgets_from_device_types(self.root_toggle_frame.contents)

        self.update_canvas_size()

    def update_canvas_size(self, event=None):
        self.inner_frame.update_idletasks()
        self.canvas.update_idletasks()

        if self.hide_scrollbar:
            if self.inner_frame.winfo_reqheight() > self.canvas.winfo_height():
                self.scrollbar.pack(side="right", fill="y")
            else:
                self.scrollbar.pack_forget()
            self.canvas.update_idletasks()

        self.canvas.config(
            width=self.inner_frame.winfo_reqwidth(),
            scrollregion=self.canvas.bbox("all"),
        )
