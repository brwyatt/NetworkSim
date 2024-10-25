from typing import List
from typing import Type


def get_all_subclasses(cls: Type) -> List[Type]:
    subclasses = []
    for subclass in cls.__subclasses__():
        subclasses.append(subclass)
        subclasses.extend(get_all_subclasses(subclass))
    return subclasses
