import time
import tkinter as tk
from tkinter import font


class SimControlsPane(tk.Frame):
    def __init__(self, master=None, *args, sim):
        super().__init__(master=master)

        self.sim = sim

        self.build()

    def step(self):
        self.step_count.set(self.step_count.get() + 1)
        self.resize_step_counters()
        self.update()
        self.update_idletasks()

    def step_x(self, x: int = 1):
        if self.stop:
            return
        self.disable_steps()
        self.master.step()
        self.step_multi_counter.set(self.step_multi_counter.get() + 1)
        if x <= 1:
            self.enable_steps()
            return
        self.after_id = self.after(250, self.step_x, x - 1)

    def step_multi(self):
        self.stop = False
        self.step_multi_counter.set(0)
        self.step_x(self.step_multi_count.get())

    def stop_stepping(self):
        self.stop = True
        if self.after_id is not None:
            self.after_cancel(self.after_id)
        self.enable_steps()

    def build(self):
        self.step_label = tk.Label(self, text="Current Step:")
        self.step_label.pack(side="left", padx=5, pady=5)
        self.step_count = tk.IntVar(self, value=0)
        self.step_counter = tk.Entry(
            self,
            textvariable=self.step_count,
            state="disabled",
        )
        self.step_counter.pack(side="left", padx=5, pady=5)

        tk.Frame(self, bg="black", width=3).pack(
            side="left",
            fill="y",
            padx=5,
            pady=5,
        )

        self.step_button = tk.Button(
            self,
            text="Step Once",
            command=self.master.step,
        )
        self.step_button.pack(side="left", padx=5, pady=5)

        tk.Frame(self, bg="black", width=3).pack(
            side="left",
            fill="y",
            padx=5,
            pady=5,
        )

        self.step_multi_button = tk.Button(
            self,
            text="Step:",
            command=self.step_multi,
        )
        self.step_multi_button.pack(side="left", padx=5, pady=5)
        self.step_multi_counter = tk.IntVar(self, value=0)
        self.step_multi_counter_display = tk.Entry(
            self,
            textvariable=self.step_multi_counter,
            state="disabled",
        )
        self.step_multi_counter_display.pack(side="left", padx=5, pady=5)
        tk.Label(self, text="/").pack(side="left")
        self.step_multi_count = tk.IntVar(self, value=5)
        self.step_multi_count_input = tk.Entry(
            self,
            textvariable=self.step_multi_count,
            validate="key",
            validatecommand=(
                self.master.register(lambda P: P.isdigit() or P == ""),
                "%P",
            ),
        )
        self.step_multi_count_input.pack(side="left", padx=5, pady=5)

        self.resize_step_counters()

        tk.Frame(self, bg="black", width=3).pack(
            side="left",
            fill="y",
            padx=5,
            pady=5,
        )

        self.stop_button = tk.Button(
            self,
            text="Stop",
            state="disabled",
            command=self.stop_stepping,
        )
        self.stop_button.pack(side="left", padx=5, pady=5)
        self.stop = False
        self.after_id = None

        tk.Frame(self, bg="black", width=3).pack(
            side="left",
            fill="y",
            padx=5,
            pady=5,
        )

        tk.Frame(self, width=200).pack(side="left", fill="both")

        self.reset_view = tk.Button(
            self,
            text="Reset View",
            command=self.master.viewPort.reset_view,
        )
        self.reset_view.pack(side="right", padx=5, pady=5)
        tk.Frame(self, bg="black", width=3).pack(
            side="right",
            fill="y",
            padx=5,
            pady=5,
        )

    def enable_steps(self):
        self.step_button.configure(state="normal")
        self.step_multi_button.configure(state="normal")
        self.step_multi_count_input.configure(state="normal")
        self.stop_button.configure(state="disabled")

    def disable_steps(self):
        self.step_button.configure(state="disabled")
        self.step_multi_button.configure(state="disabled")
        self.step_multi_count_input.configure(state="disabled")
        self.stop_button.configure(state="normal")

    def resize_step_counters(self):
        # Global step counter
        entry_font = font.Font(font=self.step_counter["font"])
        text_width = entry_font.measure("0" * len(str(self.step_count.get())))
        self.step_counter.config(width=text_width // entry_font.measure("0"))

        # Multi-step counters
        text_width = entry_font.measure(
            "0" * len(str(self.step_multi_counter.get())),
        )
        self.step_multi_counter_display.config(
            width=text_width // entry_font.measure("0"),
        )
        text_width = entry_font.measure("0" * 4)
        self.step_multi_count_input.config(
            width=text_width // entry_font.measure("0"),
        )
