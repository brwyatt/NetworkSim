import tkinter as tk


class SimControlsPane(tk.Frame):
    def __init__(self, master=None, *args, sim):
        super().__init__(master=master)

        self.sim = sim

        self.build()

    def build(self):
        self.step_button = tk.Button(self, text="Step")
        self.step_button.pack()
