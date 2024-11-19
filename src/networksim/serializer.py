from uuid import uuid4


class Serializable:
    @property
    def id(self):
        if not hasattr(self, "_id"):
            self._id = str(uuid4())
        return self._id

    def serialize(self, context=None):
        if context is None:
            context = {}
        data = {
            "id": self.id,
            "type": f"{self.__class__.__module__}:{self.__class__.__name__}",
            "properties": {},
        }

        for name, value in self.__dict__.items():
            print(f"{self.id}: {name}")
            serialized_value, serialized_context = serialize(
                value,
                context=context,
            )
            data["properties"][name] = serialized_value
            context = {**context, **serialized_context}

        return data, context

    @classmethod
    def deserialize(cls, properties, context=None):
        if context is None:
            context = {}


def serialize(value, context=None):
    if context is None:
        context = {}
    if isinstance(value, (int, str, float)):
        return value, context
    if isinstance(value, (bytes)):
        return {
            "type": "bytes",
            "value": "".join(format(x, "02x") for x in value),
        }, context
    if isinstance(value, Serializable):
        if value.id in context:
            return {"type": "REF", "id": value.id}, context
        serialized_value, serialized_context = value.serialize(context=context)
        return {"type": "REF", "id": value.id}, {
            **context,
            **serialized_context,
            value.id: serialized_value,
        }
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
        data = {
            "type": f"{value.__class__.__module__}:{value.__class__.__name__}",
            "properties": {},
        }
        for prop_name, prop_value in value.__dict__.items():
            serialized_value, serialized_context = serialize(
                prop_value,
                context=context,
            )
            data["properties"][prop_name] = serialized_value
            context = {**context, **serialized_context}
        return data, context

    raise TypeError(f'Unable to serialize type "{type(value)}"')
