import tkinter as tk


class ErrorWindow(tk.Toplevel):
    def __init__(
        self,
        master=None,
        *args,
        text="",
    ):
        super().__init__(master=master)

        self.transient(master.winfo_toplevel())
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.grid_columnconfigure(0, weight=1)

        # Leaving first row vacant for now (maybe add label later?)

        self.text = tk.Label(self, text=text)
        self.text.grid(column=0, row=0, sticky="SE")
        self.okay = tk.Button(self, text="OK", command=self.close)
        self.okay.grid(column=0, row=1)

        self.resizable(False, False)
        self.grab_set()

    def close(self):
        # re-activate parent window
        self.grab_release()
        # just in case
        self.master.winfo_toplevel().deiconify()
        self.destroy()
