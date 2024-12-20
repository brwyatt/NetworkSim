import inspect
import tkinter as tk
import typing
from enum import Enum
from enum import EnumMeta as EnumType
from typing import get_args
from typing import get_origin
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import Union

from networksim.addr import Addr
from networksim.addr.ipaddr import IPAddr
from networksim.addr.macaddr import MACAddr
from networksim.packet import Packet
from networksim.packet.payload import Payload
from networksim.utils import get_all_subclasses


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


class IPAddrVar(tk.StringVar):
    def get(self, *args, **kwargs):
        val = super().get(*args, **kwargs)
        return IPAddr.from_str(val)


class MACAddrVar(tk.StringVar):
    def get(self, *args, **kwargs):
        val = super().get(*args, **kwargs)
        return MACAddr.from_str(val)


def get_var_fields(
    master,
    param_type,
    sticky="EW",
    skip_subclassbuilder=False,
):
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
                master.register(lambda P: P.isdigit() or P == ""),
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
    elif param_type is IPAddr:
        var = IPAddrVar()
        field = tk.Entry(master, textvariable=var)
    elif param_type is MACAddr:
        var = MACAddrVar()
        field = tk.Entry(master, textvariable=var)
    elif get_origin(param_type) is list:
        var = field = ListBuilderFrame(master, cls=get_args(param_type)[0])
    elif get_origin(param_type) is Union:
        args = [x for x in get_args(param_type) if x is not type(None)]
        var = field = SelectObjectBuilderFrame(
            master,
            classes=args,
        )
    elif param_type in [Packet, Payload, Addr] and not skip_subclassbuilder:
        var = field = SelectSubclassBuilderFrame(master, base_class=param_type)
    elif isinstance(param_type, EnumType):
        var = field = EnumSelect(master, param_type)
    else:
        var = field = ObjectBuilderFrame(master, cls=param_type)

    return var, field, sticky


class EnumSelect(tk.OptionMenu):
    def __init__(self, master, enum: EnumType):
        self.enum = enum
        self.selected = tk.StringVar(master, value="")
        self.selected.trace_add("write", self.changed)
        super().__init__(master, self.selected, *[x.name for x in list(enum)])

    def changed(self, *args):
        self.update_size()

    def update_size(self):
        toplevel = self.winfo_toplevel()
        toplevel.update_idletasks()
        toplevel.update()
        reqwidth = toplevel.winfo_reqwidth()
        reqheight = toplevel.winfo_reqheight()
        self.winfo_toplevel().geometry(f"{reqwidth}x{reqheight}")

    def get(self):
        if self.selected.get():
            return getattr(self.enum, self.selected.get()).value


class ObjectBuilderFrame(tk.Frame):
    def __init__(
        self,
        master=None,
        *args,
        cls: Type,
        ignore_list: Optional[List[str]] = None,
    ):
        super().__init__(master=master)
        self.cls = cls
        self.ignore_list = set(ignore_list if ignore_list is not None else [])
        self.ignore_list.add("args")
        self.ignore_list.add("kwargs")
        self.ignore_list.add("kwds")

        self.build_fields()

    def build_fields(self):
        self.fields = {}

        self.columnconfigure(2, weight=1)

        row = 0
        sig = inspect.signature(self.cls)
        for name, param in sig.parameters.items():
            if name in self.ignore_list:
                continue
            optional = get_origin(param.annotation) is Union and type(
                None,
            ) in get_args(param.annotation)
            param_type = (
                param.annotation
                if not optional or len(get_args(param.annotation)) > 2
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

            print(
                f"FIELD: {name} TYPE: {param_type} DEFAULT: {self.fields[name].get('default', 'NO DEFAULT')}",
            )
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

    def get_toggle_handler(self, var, label, field):
        def handler():
            if var.get() == 0:
                label.config(state="disabled")
                field.config(state="disabled")
            else:
                label.config(state="normal")
                field.config(state="normal")

        return handler

    def set(self, val):
        print(
            f"WARNING: `set()` was called on Object Builder for {self.cls.__name__} (ignoring!)",
        )

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
            elif var_type is Union:
                var_type = get_args(v["type"])

            # Handle cases where we get something weird back, like an int for a bool
            if not isinstance(value, var_type):
                value = var_type(value)
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


def resolve_references(ref):
    if isinstance(ref, typing.ForwardRef):
        return ref._evaluate(globals(), locals(), frozenset())
    return ref


class SelectObjectBuilderFrame(tk.Frame):
    def __init__(
        self,
        master=None,
        *args,
        classes: Union[List[Type], List[Tuple[str, Type]]],
        skip_subclassbuilder=False,
    ):
        super().__init__(master=master)
        self.classes = {}
        for x in classes:
            if isinstance(x, tuple):
                self.classes[x[0]] = x[1]
            else:
                x = resolve_references(x)
                self.classes[x.__name__] = x
        self.skip_subclassbuilder = skip_subclassbuilder

        self.build_fields()

    def build_fields(self):
        self.columnconfigure(1, weight=1)

        self.type_label = tk.Label(self, text="Type: ")
        self.type_label.grid(row=0, column=0, sticky="NE")

        self.selected_type = tk.StringVar(self, value="")
        self.type_selector = tk.OptionMenu(
            self,
            self.selected_type,
            *[x for x in self.classes.keys()],
        )
        self.selected_type.trace_add("write", self.type_changed)
        self.type_selector.grid(row=0, column=1, sticky="NW")

        self.object_var = tk.StringVar(self, value="")
        self.object_frame = tk.Label(self, text="Select Type")
        self.object_frame.grid(row=1, column=1, sticky="NW")

    def type_changed(self, *args):
        self.object_frame.destroy()
        self.object_var, self.object_frame, sticky = get_var_fields(
            self,
            self.classes[self.selected_type.get()],
            skip_subclassbuilder=self.skip_subclassbuilder,
        )
        self.object_frame.grid(row=1, column=1, sticky=sticky)

        self.update_size()

    def config(self, *args, state=None, **kwargs):
        super().config(*args, **kwargs)
        if state is not None:
            for widget in [
                self.type_label,
                self.type_selector,
                self.object_frame,
            ]:
                widget.config(state=state)

    def update_size(self):
        toplevel = self.winfo_toplevel()
        toplevel.update_idletasks()
        toplevel.update()
        reqwidth = toplevel.winfo_reqwidth()
        reqheight = toplevel.winfo_reqheight()
        self.winfo_toplevel().geometry(f"{reqwidth}x{reqheight}")

    def get(self):
        if isinstance(self.object_frame, tk.Label):
            return None
        return self.object_var.get()


class SelectSubclassBuilderFrame(SelectObjectBuilderFrame):
    def __init__(
        self,
        master=None,
        *args,
        base_class: Type,
    ):
        super().__init__(
            master=master,
            classes=get_all_subclasses(base_class, named=True),
            skip_subclassbuilder=True,
        )
