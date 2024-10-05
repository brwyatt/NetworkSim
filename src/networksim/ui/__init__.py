import tkinter as tk
import tkinter.dnd as dnd
from collections import defaultdict

import pkg_resources
from networksim.simulation import Simulation


class ToggleFrame(tk.Frame):
    def __init__(self, master=None, title="TOGGLE"):
        super().__init__(master=master)

        bg_color = "blue"

        self.show = tk.IntVar()
        self.show.set(0)

        self.columnconfigure(0, weight=1)

        self.title_frame = tk.Frame(
            self,
            relief="raised",
            borderwidth=1,
            bg=bg_color,
        )
        self.title_frame.grid(row=0, column=0, sticky="NEW")
        self.title_frame.columnconfigure(0, weight=1)

        self.title_text = tk.Label(self.title_frame, text=title, bg=bg_color)
        self.title_text.grid(row=0, column=0, sticky="W")

        self.toggle_button = tk.Checkbutton(
            self.title_frame,
            text="+",
            variable=self.show,
            command=self.toggle,
            bg=bg_color,
        )
        self.toggle_button.grid(row=0, column=1, sticky="E")

        self.content_holder = tk.Frame(self, bg=bg_color)
        self.content_holder.columnconfigure(1, weight=1)

        self.content_spacer = tk.Label(
            self.content_holder,
            width=2,
            bg=bg_color,
        )
        self.content_spacer.grid(row=0, column=0, sticky="W")
        self.contents = tk.Frame(self.content_holder)
        self.contents.grid(row=0, column=1, sticky="EW")

        self.toggle()

    def toggle(self):
        if bool(self.show.get()):
            self.content_holder.grid(row=1, column=0, sticky="NSEW")
            self.toggle_button.configure(text="-")
        else:
            self.content_holder.grid_forget()
            self.toggle_button.configure(text="+")


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
        self.create_widgets_from_device_types(self)


class ViewPane(tk.Canvas):
    def __init__(self, master=None):
        super().__init__(master=master, width=400, height=400, bg="white")

        # Create a rectangle
        self.rect = self.create_rectangle(50, 50, 100, 100, fill="blue")

        # Bind mouse events to the rectangle
        self.tag_bind(self.rect, "<ButtonPress-1>", self.on_start)
        self.tag_bind(self.rect, "<B1-Motion>", self.on_drag)

    def on_start(self, event):
        # Record the initial mouse position
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_drag(self, event):
        # Calculate the distance moved
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y

        # Move the rectangle
        self.move(self.rect, dx, dy)

        # Update the initial mouse position
        self.drag_start_x = event.x
        self.drag_start_y = event.y


class SimControlsPane(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master=master)
        self.build()

    def build(self):
        self.step_button = tk.Button(self, text="Step")
        self.step_button.pack()


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

    def build(self):
        self.objectList = ObjectListPane(self)
        self.objectList.grid(column=0, row=0, rowspan=2, sticky="NSEW")

        self.viewPort = ViewPane(self)
        self.viewPort.grid(column=1, row=0, sticky="NSEW")

        self.controlsPane = SimControlsPane(self)
        self.controlsPane.grid(column=1, row=1, sticky="NSEW")


def start_ui():
    ui = NetworkSimUI()
    ui.mainloop()
