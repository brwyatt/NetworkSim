import inspect
import tkinter as tk
from typing import get_args
from typing import get_origin
from typing import Union


class AddWindow(tk.Toplevel):
    def __init__(self, master=None, *args, device_cls, add_handler):
        super().__init__(master=master)

        self.device_cls = device_cls
        self.add_to_view = add_handler

        self.title(f"Adding {device_cls.__name__}")
        self.transient(master.winfo_toplevel())
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Leaving first row vacant for now (maybe add label later?)

        self.fields_frame = tk.Frame(self)
        self.fields_frame.grid(column=0, row=1, columnspan=2, sticky="NSEW")

        self.okay = tk.Button(self, text="OK", command=self.submit)
        self.okay.grid(column=0, row=2, sticky="SE")
        self.cancel = tk.Button(self, text="Cancel", command=self.close)
        self.cancel.grid(column=1, row=2, sticky="SW")

        self.build_fields()

        self.grab_set()

    def int_validate(self, P):
        return P.isdigit()

    def build_fields(self):
        self.fields = {}

        self.fields_frame.columnconfigure(2, weight=1)

        row = 0
        sig = inspect.signature(self.device_cls)
        for name, param in sig.parameters.items():
            optional = get_origin(param.annotation) is Union and type(
                None,
            ) in get_args(param.annotation)
            param_type = (
                param.annotation
                if not optional
                else get_args(param.annotation)[0]
            )

            self.fields[name] = {
                "title": name.replace("_", " ").title(),
                "optional": optional,
                "type": param_type,
                "enabled": tk.IntVar(value=0 if optional else 1),
                "widgets": {},
            }

            if param.default is not inspect.Parameter.empty:
                self.fields[name]["default"] = param.default

            label = tk.Label(
                self.fields_frame,
                text=self.fields[name]["title"] + ": ",
                state="normal" if not optional else "disabled",
            )
            label.grid(row=row, column=1, sticky="E")
            self.fields[name]["widgets"]["label"] = label

            sticky = "EW"
            if param_type is str:
                var = tk.StringVar()
                field = tk.Entry(self.fields_frame, textvariable=var)
            elif param_type is int:
                var = tk.IntVar()
                field = tk.Spinbox(
                    self.fields_frame,
                    textvariable=var,
                    validate="key",
                    validatecommand=(
                        self.fields_frame.register(self.int_validate),
                        "%P",
                    ),
                )
            elif param_type is bool:
                sticky = "W"
                var = tk.IntVar()
                field = tk.Checkbutton(
                    self.fields_frame,
                    variable=var,
                )
            else:
                var = tk.StringVar()
                field = tk.Entry(self.fields_frame)

            field.grid(row=row, column=2, sticky=sticky)
            field.config(state="normal" if not optional else "disabled")
            self.fields[name]["widgets"]["field"] = field
            self.fields[name]["value"] = var

            if self.fields[name].get("default") is not None:
                if param_type is bool:
                    var.set(1 if self.fields[name]["default"] else 0)
                else:
                    var.set(self.fields[name]["default"])

            if optional:
                toggle = tk.Checkbutton(
                    self.fields_frame,
                    variable=self.fields[name]["enabled"],
                    command=self.get_toggle_handler(
                        self.fields[name]["enabled"],
                        label,
                        field,
                    ),
                )
                toggle.grid(row=row, column=0)
                self.fields[name]["widgets"]["toggle"] = toggle

            row += 1
        # TODO: add a "port config" section to manually add ports
        # ... need the port configuring window first, though

    def get_toggle_handler(self, var, label, field):
        def handler():
            if var.get() == 0:
                label.config(state="disabled")
                field.config(state="disabled")
            else:
                label.config(state="normal")
                field.config(state="normal")

        return handler

    def submit(self):
        params = {}
        print(f"Creating {self.device_cls.__name__} with parameters:")
        for k, v in self.fields.items():
            enabled = bool(v["enabled"].get())
            if not enabled:
                continue
            params[k] = v["type"](v["value"].get())
            print(f" * {k}: {params[k]}")

        self.add_to_view(self.device_cls(**params))
        self.close()

    def close(self):
        # re-activate parent window
        self.grab_release()
        # just in case
        self.master.winfo_toplevel().deiconify()
        self.destroy()
