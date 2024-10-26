from typing import List
from typing import Type


def get_all_subclasses(
    cls: Type,
    named: bool = False,
    prefix: str = "1",
) -> List[Type]:
    subclasses = [(f"{prefix}) {cls.__name__}", cls) if named else cls]
    index = 0
    for subclass in cls.__subclasses__():
        index += 1
        subclasses.extend(
            get_all_subclasses(
                subclass,
                named=named,
                prefix=f"{prefix}.{index}",
            ),
        )
    return subclasses
