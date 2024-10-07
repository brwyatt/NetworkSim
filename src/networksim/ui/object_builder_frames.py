import inspect
import tkinter as tk
from typing import get_args
from typing import get_origin
from typing import Type
from typing import Union


class ListBuilderFrame(tk.Frame):
    def __init__(self, master=None, *args, cls: Type):
        super().__init__(master=master)
        self.cls = cls

        self.build()

    def build(self):
        self.fields = []

        self.columnconfigure(0, weight=1)

        self.list_frame = tk.Frame(self)
        self.list_frame.grid(row=0, column=0, sticky="EW")

        self.add_button = tk.Button(
            self,
            text="Add Item",
            command=self.add_item,
        )
        self.add_button.grid(row=1, column=0, sticky="W")

    def get_del_handler(self, widget):
        def handler():
            index = widget.grid_info()["row"]

            field = self.fields[index]
            del self.fields[index]
            field["del_btn"].destroy()
            field["label"].destroy()
            field["field"].destroy()

            for field in self.fields[index:]:
                row = field["del_btn"].grid_info()["row"] - 1
                field["del_btn"].grid(row=row)
                field["label"].grid(row=row)
                field["label"].configure(text=f"{row}: ")
                field["field"].grid(row=row)

            self.update_size()

        return handler

    def update_size(self):
        toplevel = self.winfo_toplevel()
        toplevel.update_idletasks()
        toplevel.update()
        reqwidth = toplevel.winfo_reqwidth()
        reqheight = toplevel.winfo_reqheight()
        self.winfo_toplevel().geometry(f"{reqwidth}x{reqheight}")

    def add_item(self):
        row = len(self.fields)

        del_btn = tk.Button(self.list_frame, text="X")
        del_btn.config(command=self.get_del_handler(del_btn))
        del_btn.grid(row=row, column=0, sticky="N")

        label = tk.Label(self.list_frame, text=f"{row}: ")
        label.grid(row=row, column=1, sticky="NE")

        var, field, sticky = (
            *get_var_fields(
                self.list_frame,
                self.cls,
            ),
        )

        field.grid(row=row, column=2, sticky=sticky)

        field_def = {
            "del_btn": del_btn,
            "label": label,
            "var": var,
            "field": field,
        }

        self.fields.append(field_def)

        self.update_size()

    def get(self):
        return [x["var"].get() for x in self.fields]

    def config(self, *args, state=None, **kwargs):
        super().config(*args, **kwargs)
        if state is not None:
            self.add_button.config(state=state)
            for field in self.fields:
                field["del_btn"].config(state=state)
                field["label"].config(state=state)
                field["field"].config(state=state)


def get_var_fields(master, param_type, sticky="EW"):
    if param_type in (str, bytes):
        var = tk.StringVar()
        field = tk.Entry(master, textvariable=var)
    elif param_type is int:
        var = tk.IntVar()
        field = tk.Spinbox(
            master,
            textvariable=var,
            validate="key",
            validatecommand=(
                master.register(lambda P: P.isdigit()),
                "%P",
            ),
        )
    elif param_type is bool:
        sticky = "W"
        var = tk.IntVar()
        field = tk.Checkbutton(
            master,
            variable=var,
        )
    elif get_origin(param_type) is list:
        var = field = ListBuilderFrame(master, cls=get_args(param_type)[0])
    else:
        var = field = ObjectBuilderFrame(master, cls=param_type)

    return var, field, sticky


class ObjectBuilderFrame(tk.Frame):
    def __init__(self, master=None, *args, cls: Type):
        super().__init__(master=master)
        self.cls = cls

        self.build_fields()

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
            label.grid(row=row, column=1, sticky="NE")
            self.fields[name]["widgets"]["label"] = label

            sticky = "EW"
            var, field, sticky = get_var_fields(self, param_type, sticky)

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
                toggle.grid(row=row, column=0, sticky="N")
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

            # Get the real type
            var_type = get_origin(v["type"])
            if var_type is None:
                var_type = v["type"]

            # Handle cases where we get something weird back, like an int for a bool
            if not isinstance(value, var_type):
                value = var_type(v["value"].get())
            params[k] = value
            print(f" * {k}: {params[k]}")

        return self.cls(**params)

    def config(self, *args, state=None, **kwargs):
        super().config(*args, **kwargs)
        if state is not None:
            for field in self.fields.values():
                widgets = field.get("widgets", {})
                for name, widget in widgets.items():
                    widget.config(
                        state=(
                            state
                            if name == "toggle" or bool(field["enabled"].get())
                            else "disabled"
                        ),
                    )
