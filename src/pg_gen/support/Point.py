from dataclasses import dataclass
from enum import Enum
from math import floor, isnan, nan, sqrt
from typing import ClassVar, Dict, override

from .Direction import Direction


class Axis(Enum):
    COLUMN = 0
    ROW = 1

    @property
    def vector(self):
        return Point.DOWN if self == Axis.COLUMN else Axis.ROW

    @property
    def cross(self):
        return Axis.ROW if self == Axis.COLUMN else Axis.COLUMN


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def __add__(self, other: "Point"):
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Point"):
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, other: "Point | float | int"):
        if isinstance(other, Point):
            return Point(self.x * other.x, self.y * other.y)
        elif isinstance(other, (int, float)):  # type: ignore
            return Point(self.x * other, self.y * other)
        else:
            return NotImplemented

    def __truediv__(self, other: "Point | float | int"):
        if isinstance(other, Point):
            return Point(self.x / other.x, self.y / other.y)
        elif isinstance(other, (int, float)):  # type: ignore
            return Point(self.x / other, self.y / other)
        else:
            return NotImplemented

    def magnitude(self):
        return sqrt(self.x**2 + self.y**2)

    def dominant_size(self):
        return max(abs(self.x), abs(self.y))

    def as_mask(self):
        return Point(
            1 if self.x != 0 else 0,
            1 if self.y != 0 else 0,
        )

    def normalize(self):
        mag = self.magnitude()
        if mag == 0:
            return Point.ZERO
        return Point(self.x / mag, self.y / mag)

    def down(self):
        return Point(0, self.y)

    def right(self):
        return Point(self.x, 0)

    def floor(self):
        return Point(floor(self.x), floor(self.y))

    def round(self):
        return Point(round(self.x), round(self.y))

    def is_negative(self):
        return self.x < 0 or self.y < 0

    def abs(self):
        return Point(abs(self.x), abs(self.y))

    def quantize(self, grid: float):
        return (self * (1 / grid)).round() * grid

    def to_pygame_coordinates(self):
        x = floor(self.x + 0.0001)
        y = floor(self.y + 0.0001)

        return (x, y)

    def to_pygame_rect(self, size: "Point", scale: float = 1.0):
        # To floor our value to integer pixel coordinates we add a small constant
        # to counteract floating point imprecision and therefore prevent one-off
        # errors in position

        x = floor(self.x * scale + 0.0001)
        y = floor(self.y * scale + 0.0001)
        width = floor(size.x * scale + 0.0001)
        height = floor(size.y * scale + 0.0001)

        return (x, y, width, height)

    @staticmethod
    def from_direction(direction: Direction):
        if direction == Direction.LEFT:
            return Point.LEFT
        if direction == Direction.RIGHT:
            return Point.RIGHT
        if direction == Direction.UP:
            return Point.UP
        if direction == Direction.DOWN:
            return Point.DOWN

        assert False, "Invalid direction enum value"

    @override
    def __repr__(self) -> str:
        return f"Point({self.x:.2f}, {self.y:.2f})"

    def serialize(self):
        return {"x": self.x, "y": self.y}

    def merge(self, other: "Point"):
        return Point(
            self.x if isnan(other.x) else other.x,
            self.y if isnan(other.y) else other.y,
        )

    def __getitem__(self, axis: Axis):
        return self.right() if axis == Axis.ROW else self.down()

    @staticmethod
    def deserialize(data: Dict[str, float]):
        return Point(data["x"], data["y"])

    @staticmethod
    def min(a: "Point", b: "Point"):
        return Point(min(a.x, b.x), min(a.y, b.y))

    @staticmethod
    def max(a: "Point", b: "Point"):
        return Point(max(a.x, b.x), max(a.y, b.y))

    @staticmethod
    def max_size(a: "Point", b: "Point"):
        return Point(
            a.x if abs(a.x) > abs(b.x) else b.x,
            a.y if abs(a.y) > abs(b.y) else b.y,
        )

    ZERO: ClassVar["Point"]
    ONE: ClassVar["Point"]
    LEFT: ClassVar["Point"]
    RIGHT: ClassVar["Point"]
    UP: ClassVar["Point"]
    DOWN: ClassVar["Point"]
    NAN: ClassVar["Point"]


Point.ZERO = Point(0, 0)
Point.ONE = Point(1, 1)
Point.LEFT = Point(-1, 0)
Point.RIGHT = Point(1, 0)
Point.UP = Point(0, -1)
Point.DOWN = Point(0, 1)
Point.NAN = Point(nan, nan)
