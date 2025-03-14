from typing import Callable, Iterable


def find_index_by_predicate[T](elements: Iterable[T], predicate: Callable[[T], bool]):
    return next((i for i, element in enumerate(elements) if predicate(element)), -1)


def lerp(a: float, b: float, t: float):
    return b * t + a * (1 - t)
