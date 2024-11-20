import importlib
import inspect
from collections import namedtuple
from uuid import uuid4

from networksim.hardware.cable import Cable
from networksim.hardware.device import Device
from networksim.hardware.interface import Interface
from networksim.hwid import HWID
from networksim.ipaddr import IPAddr
from networksim.packet import Packet
from networksim.packet.payload import Payload
from networksim.simulation import Simulation


default_ref_types = (
    IPAddr,
    HWID,
    Device,
    Simulation,
    Interface,
    Cable,
    Packet,
    Payload,
)
raw_types = (int, str, float, type(None))


def _load(path):
    type_parts = path.split(":")
    module = importlib.import_module(type_parts[0])
    cls = getattr(module, type_parts[1])

    return module, cls


def serialize(value, context=None, ref_types=None):
    if context is None:
        context = {}
    if ref_types is None:
        ref_types = default_ref_types
    if isinstance(value, raw_types):
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
    if isinstance(value, (list, set, tuple)) and not hasattr(value, "_asdict"):
        # most list-like things... excluding namedtuples
        data = {
            "type": (
                "tuple"
                if isinstance(value, tuple)
                else "set" if isinstance(value, set) else "list"
            ),
            "value": [],
        }
        for i in value:
            serialized_value, serialized_context = serialize(i, context)
            context = {**context, **serialized_context}
            data["value"].append(serialized_value)
        return data, context
    if isinstance(value, type):
        data = {
            "type": "TYPE",
            "value": f"{value.__module__}:{value.__name__}",
        }
        return data, context
    if inspect.ismethod(value):
        instance, context = serialize(value.__self__, context=context)
        data = {
            "type": "METHOD",
            "method": value.__name__,
            "instance": instance,
        }
        return data, context
    if isinstance(value, object):
        if isinstance(value, ref_types):
            if not hasattr(value, "__serial_id"):
                setattr(value, "__serial_id", str(uuid4()))
            if getattr(value, "__serial_id") in context:
                return {
                    "type": "REF",
                    "id": getattr(value, "__serial_id"),
                }, context
        data = {
            "type": f"{value.__class__.__module__}:{value.__class__.__name__}",
            "properties": {},
        }
        if isinstance(value, ref_types):
            # Add incomplete dummy data to prevent recursion
            context[getattr(value, "__serial_id")] = data
        # Handle namedtuples
        props = (
            value.__dict__ if not isinstance(value, tuple) else value._asdict()
        )
        for prop_name, prop_value in props.items():
            serialized_value, context = serialize(
                prop_value,
                context=context,
            )
            data["properties"][prop_name] = serialized_value
        if isinstance(value, ref_types):
            context[getattr(value, "__serial_id")] = data
            data = {"type": "REF", "id": getattr(value, "__serial_id")}
        return data, context

    raise TypeError(f'Unable to serialize type "{type(value)}"')


def _parse_bytes(b):
    res = []
    for i in range(0, len(b), 2):
        res.append(int(b[i : i + 2], 16).to_bytes(1, "big")[0])
    return bytes(res)


def deserialize(value, context=None):  # noqa: C901
    if context is None:
        context = {}
    if isinstance(value, raw_types):
        return value, context
    if not isinstance(value, dict) or "type" not in value:
        raise TypeError(
            f"Invalid serialization object: {type(value).__name__}",
        )
    if value["type"] == "TYPE":
        module, cls = _load(value["value"])
        return cls, context
    if value["type"] == "METHOD":
        instance, context = deserialize(value["instance"], context=context)
        return getattr(instance, value["method"]), context
    if value["type"] in ["list", "set", "tuple"]:
        data = []
        for x in value.get("value", []):
            val, context = deserialize(x, context=context)
            data.append(val)
        if value["type"] == "set":
            data = set(data)
        elif value["type"] == "tuple":
            data = tuple(data)
        return data, context
    if value["type"] == "bytes":
        return _parse_bytes(value.get("value", "")), context
    if value["type"] == "dict":
        data = {}
        for x in value["items"]:
            key, context = deserialize(x[0], context=context)
            val, context = deserialize(x[1], context=context)
            data[key] = val
        return data, context
    if value["type"] == "REF":
        if value.get("id") not in context:
            raise ValueError(f"Missing REF in context: {value.get('id')}")
        data = context[value["id"]]
        if isinstance(data, dict) and data.get("type") is not None:
            return deserialize(data, context=context)
        if isinstance(data, object):
            return data, context
    if ":" in value["type"]:
        module, cls = _load(value["type"])

        # Handle namedtuples special case
        if issubclass(cls, tuple):
            sig = inspect.signature(cls.__new__)
        else:
            sig = inspect.signature(cls.__init__)

        positional_param_list = [
            param.name
            for param in sig.parameters.values()
            if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
            and param.default is param.empty
        ]

        positional_params = {}
        for k, v in value.get("properties", {}).items():
            k = k.lstrip("_")
            if k not in positional_param_list:
                continue
            v, context = deserialize(v, context=context)
            positional_params[k] = v

        inst = type(cls.__name__, (cls,), {"__module__": module.__name__})(
            **positional_params,
        )

        if "__serial_id" in value.get("properties", {}):
            # Add partial class to prevent infinite recursion
            context[value["properties"]["__serial_id"]] = inst

        if not issubclass(cls, tuple):
            # Skip for namedtuples, this will fail
            for k, v in value.get("properties", {}).items():
                v, context = deserialize(v, context=context)
                setattr(inst, k, v)

        if hasattr(inst, "__serial_id"):
            context[getattr(inst, "__serial_id")] = inst

        return inst, context

    raise ValueError(
        f"Unable to deserialize, unrecognized format or type: {type(value).__name__} - {value.get('type')}",
    )
