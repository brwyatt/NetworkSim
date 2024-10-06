import tkinter as tk


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

    def add_device(self, device):
        print(f"ADDING: {device.name}")
        self.sim.add_device(device)
        # TODO: actually add a box to the canvas linked to this object
