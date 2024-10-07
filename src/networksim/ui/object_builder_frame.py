import inspect
import tkinter as tk
from typing import get_args
from typing import get_origin
from typing import Type
from typing import Union


class ObjectBuilderFrame(tk.Frame):
    def __init__(self, master=None, *args, cls: Type):
        super().__init__(master=master)
        self.cls = cls

        self.build_fields()

    def int_validate(self, P):
        return P.isdigit()

    def build_fields(self):
        self.fields = {}

        self.columnconfigure(2, weight=1)

        row = 0
        sig = inspect.signature(self.cls)
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
                self,
                text=self.fields[name]["title"] + ": ",
                state="normal" if not optional else "disabled",
            )
            label.grid(row=row, column=1, sticky="E")
            self.fields[name]["widgets"]["label"] = label

            sticky = "EW"
            if param_type is str:
                var = tk.StringVar()
                field = tk.Entry(self, textvariable=var)
            elif param_type is int:
                var = tk.IntVar()
                field = tk.Spinbox(
                    self,
                    textvariable=var,
                    validate="key",
                    validatecommand=(
                        self.register(self.int_validate),
                        "%P",
                    ),
                )
            elif param_type is bool:
                sticky = "W"
                var = tk.IntVar()
                field = tk.Checkbutton(
                    self,
                    variable=var,
                )
            else:
                var = tk.StringVar()
                field = tk.Entry(self)

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
                    self,
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

    def get(self):
        params = {}
        print(f"Creating {self.cls.__name__} with parameters:")
        for k, v in self.fields.items():
            enabled = bool(v["enabled"].get())
            if not enabled:
                continue
            value = v["value"].get()
            if not isinstance(value, v["type"]):
                value = v["type"](v["value"].get())
            params[k] = value
            print(f" * {k}: {params[k]}")

        return self.cls(**params)
