from typing import Callable, Iterable, Sequence


def find_index_by_predicate[T](elements: Iterable[T], predicate: Callable[[T], bool]):
    return next((i for i, element in enumerate(elements) if predicate(element)), -1)


def lerp(a: float, b: float, t: float):
    return b * t + a * (1 - t)


def weighted_random[T](source: Sequence[T], t: float, key: Callable[[T], float]):
    weights = [key(v) for v in source]
    normalization_factor = 1 / sum(weights)
    weights = [v * normalization_factor for v in weights]
    for weight, element in zip(weights, source):
        t -= weight

        if t <= 0:
            return element

    return source[-1]
