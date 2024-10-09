from typing import TYPE_CHECKING

from networksim.hardware.cable import Cable
from networksim.ui.device_shape import DeviceShape

if TYPE_CHECKING:
    from networksim.ui.viewpane import ViewPane


class CableShape:
    def __init__(
        self,
        cable: Cable,
        canvas: "ViewPane",
        device_a: DeviceShape,
        device_b: DeviceShape,
    ):
        self.cable = cable
        self.canvas = canvas
        self.a = device_a
        self.b = device_b

        self.line = self.canvas.create_line(
            *self.a.get_midpoint(),
            *self.b.get_midpoint(),
            width=5,
        )

        self.canvas.tag_lower(self.line)

        self.a.add_update_handler(self.update_location)
        self.b.add_update_handler(self.update_location)

    def update_location(self):
        self.canvas.coords(
            self.line,
            *self.a.get_midpoint(),
            *self.b.get_midpoint(),
        )

    def delete(self):
        self.a.del_update_handler(self.update_location)
        self.b.del_update_handler(self.update_location)
        self.canvas.delete(self.line)
