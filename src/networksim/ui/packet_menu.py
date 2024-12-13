import inspect
import tkinter as tk
from typing import Dict
from typing import Union

from networksim.packet import Packet
from networksim.packet.payload import Payload


def create_packet_menu(
    master,
    data: Union[Packet, Payload, Dict],
) -> tk.Menu:
    menu = tk.Menu(master, tearoff=0)

    menu.add_separator()
    menu.add_command(label=data.__class__.__name__)
    menu.add_separator()

    if isinstance(data, (Packet, Payload)):
        params = inspect.signature(data.__class__).parameters
        data_dict = data.__dict__
    elif isinstance(data, dict):
        params = data
        data_dict = data

    for name in params.keys():
        if data_dict.get(name) is None:
            menu.add_command(label=name, state="disabled")
            continue

        value = data_dict.get(name)
        if isinstance(value, (Packet, Payload, dict)):
            sub_menu = create_packet_menu(menu, value)
        else:
            sub_menu = tk.Menu(menu, tearoff=0)
            sub_menu.add_command(label=str(value))
        menu.add_cascade(
            label=f"{name} [{type(value).__name__}]",
            menu=sub_menu,
        )

    return menu
