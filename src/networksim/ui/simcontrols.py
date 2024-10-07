import tkinter as tk


class SimControlsPane(tk.Frame):
    def __init__(self, master=None, *args, sim):
        super().__init__(master=master)

        self.sim = sim

        self.build()

    def build(self):
        self.step_button = tk.Button(self, text="Step", command=self.sim.step)
        self.step_button.pack(side="left")
        self.show_button = tk.Button(self, text="Show", command=self.sim.show)
        self.show_button.pack(side="left")
