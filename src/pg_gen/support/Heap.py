from dataclasses import dataclass
from math import inf
from typing import override

NOT_IN_HEAP = -1


@dataclass
class HeapItem:
    priority: float
    heap_index: int = NOT_IN_HEAP


def _get_parent_index(index: int):
    return (index - 1) // 2


def _get_left_index(index: int):
    return index * 2 + 1


def _get_right_index(index: int):
    return index * 2 + 2


class Heap[T: HeapItem]:
    def __init__(self):
        self._data: list[T] = []

    def add(self, item: T):
        exists = item.heap_index != NOT_IN_HEAP
        if exists:
            raise Exception("Item is already in a heap")

        item.heap_index = len(self._data)
        self._data.append(item)
        self._bubble_up(item)

    def remove(self, item: T):
        exists = item.heap_index != NOT_IN_HEAP
        if not exists:
            raise Exception("Item is not in a heap")

        last_item = self._data[-1]
        if last_item is item:
            self._data.pop()
            item.heap_index = NOT_IN_HEAP
            return

        self._swap(last_item, item)
        item.heap_index = NOT_IN_HEAP
        self._data.pop()

        self._bubble_down(last_item)

    def update_item(self, item: T):
        if item.heap_index == NOT_IN_HEAP:
            self.add(item)
            return

        self._bubble_up(item)
        self._bubble_down(item)

    def pop(self):
        if len(self._data) == 0:
            raise Exception("Heap is empty")

        first = self._data[0]
        self.remove(first)
        return first

    @override
    def __repr__(self):
        return self._data.__repr__()

    def __len__(self):
        return self._data.__len__()

    def _swap(self, itemA: T, itemB: T):
        self._data[itemA.heap_index] = itemB
        self._data[itemB.heap_index] = itemA

        itemA.heap_index, itemB.heap_index = itemB.heap_index, itemA.heap_index

    def _bubble_up(self, item: T):
        while item.heap_index != 0:
            parent = self._data[_get_parent_index(item.heap_index)]
            if parent.priority > item.priority:
                self._swap(item, parent)
            else:
                break

    def _bubble_down(self, item: T):
        while True:
            left_index = _get_left_index(item.heap_index)
            right_index = _get_right_index(item.heap_index)

            left_child = self._data[left_index] if left_index < len(self._data) else None
            right_child = self._data[right_index] if right_index < len(self._data) else None

            left_priority = left_child.priority if left_child is not None else inf
            right_priority = right_child.priority if right_child is not None else inf

            priority = item.priority

            if left_priority < priority and left_priority <= right_priority:
                assert left_child is not None
                self._swap(left_child, item)
            elif right_priority < priority and right_priority < left_priority:
                assert right_child is not None
                self._swap(right_child, item)
            else:
                break
