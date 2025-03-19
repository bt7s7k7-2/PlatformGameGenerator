from dataclasses import dataclass
from typing import ClassVar

from .support import lerp


@dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int

    WHITE: ClassVar["Color"]
    BLACK: ClassVar["Color"]
    RED: ClassVar["Color"]
    GREEN: ClassVar["Color"]
    BLUE: ClassVar["Color"]
    YELLOW: ClassVar["Color"]
    CYAN: ClassVar["Color"]
    MAGENTA: ClassVar["Color"]
    ORANGE: ClassVar["Color"]

    def to_pygame_color(self, opacity: int | None = None):
        if opacity is not None:
            return (self.r, self.g, self.b, opacity)
        return (self.r, self.g, self.b)

    def __mul__(self, other: float | int):
        return Color(int(self.r * other), int(self.g * other), int(self.b * other))

    def mix(self, other: "Color", t: float):
        return Color(int(lerp(self.r, other.r, t)), int(lerp(self.g, other.g, t)), int(lerp(self.b, other.b, t)))


Color.WHITE = Color(255, 255, 255)
Color.BLACK = Color(0, 0, 0)
Color.RED = Color(255, 0, 0)
Color.GREEN = Color(0, 255, 0)
Color.BLUE = Color(0, 0, 255)
Color.YELLOW = Color(255, 255, 0)
Color.CYAN = Color(0, 255, 255)
Color.MAGENTA = Color(255, 0, 255)
Color.ORANGE = Color(255, 127, 0)
