import tkinter as tk


class SimControlsPane(tk.Frame):
    def __init__(self, master=None, *args, sim):
        super().__init__(master=master)

        self.sim = sim

        self.build()

    def step(self):
        pass

    def build(self):
        self.step_button = tk.Button(
            self,
            text="Step",
            command=self.master.step,
        )
        self.step_button.pack(side="left")

        self.show_button = tk.Button(self, text="Show", command=self.sim.show)
        self.show_button.pack(side="left")

        self.reset_view = tk.Button(
            self,
            text="Reset View",
            command=self.master.viewPort.reset_view,
        )
        self.reset_view.pack(side="right")
