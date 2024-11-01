from typing import Callable, Iterable

from .Point import Point


def is_intersection(pos_a: Point, size_a: Point, pos_b: Point, size_b: Point):
    end_a = pos_a + size_a
    end_b = pos_b + size_b

    return (pos_a.x <= end_b.x and pos_b.x <= end_a.x) and (pos_a.y <= end_b.y and pos_b.y <= end_a.y)


def resolve_intersection(pos_a: Point, size_a: Point, pos_b: Point, size_b: Point):
    end_a = pos_a + size_a
    end_b = pos_b + size_b

    move_left = end_a.x - pos_b.x
    move_right = end_b.x - pos_a.x

    move_up = end_a.y - pos_b.y
    move_down = end_b.y - pos_a.y

    minimum_displacement = min(move_left, move_right, move_down, move_up)

    if minimum_displacement < 0:
        # If any of the intersection resolution offsets are negative
        # there is no intersection, therefore no need for resolution
        return Point.ZERO

    # Always minimise the needed displacement to resolve intersection
    if minimum_displacement == move_left:
        return Point(-move_left, 0)
    elif minimum_displacement == move_right:
        return Point(move_right, 0)
    elif minimum_displacement == move_down:
        return Point(0, move_down)
    elif minimum_displacement == move_up:
        return Point(0, -move_up)

    raise ValueError("Invalid retuned value from min in resolve_intersection")


def find_index_by_predicate[T](elements: Iterable[T], predicate: Callable[[T], bool]):
    return next((i for i, element in enumerate(elements) if predicate(element)), -1)


def lerp(a: float, b: float, t: float):
    return b * t + a * (1 - t)
