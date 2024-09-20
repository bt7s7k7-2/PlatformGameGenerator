from dataclasses import dataclass
from math import sqrt
from typing import ClassVar


@dataclass(frozen=True)
class Point:
    x: float = 0
    y: float = 0

    def __add__(self, other: "Point") -> "Point":
        return Point(self.x + other.x, self.y + other.y)

    def __mul__(self, other: "Point | float | int") -> "Point":
        if isinstance(other, Point):
            return Point(self.x * other.x, self.y * other.y)
        elif isinstance(other, (int, float)):
            return Point(self.x * other, self.y * other)
        else:
            return NotImplemented

    def magnitude(self) -> float:
        return sqrt(self.x**2 + self.y**2)

    def normalize(self) -> "Point":
        mag = self.magnitude()
        if mag == 0:
            raise ValueError("Cannot normalize a zero vector")
        return Point(self.x / mag, self.y / mag)

    ZERO: ClassVar["Point"]
    ONE: ClassVar["Point"]


Point.ZERO = Point(0, 0)
Point.ONE = Point(1, 1)
