import tkinter as tk


class ToggleFrame(tk.Frame):
    def __init__(
        self,
        master=None,
        title="TOGGLE",
        show_default=False,
        toggle_update=None,
    ):
        super().__init__(master=master)

        bg_color = "blue"

        # Invert, because we render by calling `toggle()`
        self.show = not show_default

        self.toggle_update = toggle_update

        self.columnconfigure(0, weight=1)

        self.title_frame = tk.Frame(
            self,
            relief="raised",
            borderwidth=1,
            bg=bg_color,
        )
        self.title_frame.grid(row=0, column=0, sticky="NEW")
        self.title_frame.columnconfigure(0, weight=1)

        self.title_button = tk.Button(
            self.title_frame,
            text="* " + title,
            bg=bg_color,
            anchor="w",
            command=self.toggle,
        )
        self.title_button.grid(row=0, column=0, sticky="EW")

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
        self.show = not self.show
        button_text = list(self.title_button.cget("text"))
        if self.show:
            self.content_holder.grid(row=1, column=0, sticky="NSEW")
            button_text[0] = "-"
        else:
            self.content_holder.grid_forget()
            button_text[0] = "+"
        self.title_button.configure(text="".join(button_text))

        if self.toggle_update is not None:
            self.toggle_update()
