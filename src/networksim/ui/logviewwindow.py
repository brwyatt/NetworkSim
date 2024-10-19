import tkinter as tk
from typing import List


class LogViewWindow(tk.Toplevel):
    def __init__(
        self,
        master=None,
        *args,
        title: str = "Logs",
        log: List[str] = [],
    ):
        super().__init__(master=master)
        self.title(title)

        self.protocol("WM_DELETE_WINDOW", self.close)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # Allow text area to expand

        self.label = tk.Label(self, text=title)
        self.label.grid(column=0, row=0, sticky="nw", padx=5, pady=5)

        # Create a frame for the text area and scrollbar
        text_frame = tk.Frame(self)
        text_frame.grid(column=0, row=1, sticky="nsew")

        # Create the text area
        self.text = tk.Text(text_frame, wrap=tk.WORD)
        self.text.pack(side="left", fill="both", expand=True)

        # Create a scrollbar and link it to the text area
        scrollbar = tk.Scrollbar(text_frame, command=self.text.yview)
        scrollbar.pack(side="right", fill="y")
        self.text.config(yscrollcommand=scrollbar.set)

        # Insert the text from the list
        for line in log:
            self.text.insert(tk.END, line + "\n")

        # Make read-only
        self.text.config(state="disabled")

        # Scroll to the bottom
        self.text.see(tk.END)

        self.okay = tk.Button(self, text="OK", command=self.close, pady=5)
        self.okay.grid(column=0, row=2)

        self.geometry("400x300")
        self.update_idletasks()

    def close(self):
        self.destroy()
