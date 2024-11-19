from uuid import uuid4

from networksim.hardware.cable import Cable
from networksim.hardware.device import Device
from networksim.hardware.interface import Interface
from networksim.hwid import HWID
from networksim.ipaddr import IPAddr
from networksim.simulation import Simulation


default_ref_types = (IPAddr, HWID, Device, Simulation, Interface, Cable)


def serialize(value, context=None, ref_types=None):
    if context is None:
        context = {}
    if ref_types is None:
        ref_types = default_ref_types
    if isinstance(value, (int, str, float)):
        return value, context
    if isinstance(value, (bytes)):
        return {
            "type": "bytes",
            "value": "".join(format(x, "02x") for x in value),
        }, context
    if isinstance(value, dict):
        data = {"type": "dict", "items": []}
        for k, v in value.items():
            serialized_key, serialized_key_context = serialize(k, context)
            context = {**context, **serialized_key_context}
            serialized_value, serialized_value_context = serialize(v, context)
            context = {**context, **serialized_value_context}
            data["items"].append([serialized_key, serialized_value])
        return data, context
    if isinstance(value, (list, set, tuple)):
        data = []
        for i in value:
            serialized_value, serialized_context = serialize(i, context)
            context = {**context, **serialized_context}
            data.append(serialized_value)
        return data, context
    if isinstance(value, object):
        if isinstance(value, ref_types):
            if not hasattr(value, "__serial_id"):
                value.__serial_id = str(uuid4())
            if value.__serial_id in context:
                return {"type": "REF", "id": value.__serial_id}, context
        data = {
            "type": f"{value.__class__.__module__}:{value.__class__.__name__}",
            "properties": {},
        }
        for prop_name, prop_value in value.__dict__.items():
            serialized_value, context = serialize(
                prop_value,
                context=context,
            )
            data["properties"][prop_name] = serialized_value
        if isinstance(value, ref_types):
            context[value.__serial_id] = data
            data = {"type": "REF", "id": value.__serial_id}
        return data, context

    raise TypeError(f'Unable to serialize type "{type(value)}"')
