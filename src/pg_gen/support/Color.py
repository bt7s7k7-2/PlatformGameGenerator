from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int

    WHITE: ClassVar["Color"]
    BLACK: ClassVar["Color"]

    def to_tuple(self):
        return (self.r, self.g, self.b)

    def __mul__(self, other: float | int):
        return Color(int(self.r * other), int(self.g * other), int(self.b * other))


Color.WHITE = Color(255, 255, 255)
Color.BLACK = Color(0, 0, 0)
