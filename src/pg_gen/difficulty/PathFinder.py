from dataclasses import dataclass
from time import perf_counter

from ..generation.Map import Map
from ..generation.RoomInfo import NOT_CONNECTED
from ..support.Direction import Direction
from ..support.Heap import NOT_IN_HEAP, Heap, HeapItem
from ..support.Point import Point


@dataclass(kw_only=True)
class PathFinderState(HeapItem):
    position: Point
    distance_from_start: float
    distance_to_end: float
    closed = False
    parent: "PathFinderState | None" = None

    def get_path(self):
        path: list[Point] = []
        current = self

        while True:
            path.append(current.position)
            if current.parent is None:
                break
            current = current.parent

        path.reverse()
        return path


@dataclass
class PathFinder:
    map: Map

    def find_path(self, start: Point, end: Point):
        start_time = perf_counter()
        state_cache: dict[Point, PathFinderState] = {}
        open_queue = Heap[PathFinderState]()

        def create_state(position: Point, parent: PathFinderState | None):
            distance_from_start = parent.distance_from_start + 1 if parent is not None else 0
            distance_to_end = Point.distance(position, end)

            state = PathFinderState(
                priority=distance_from_start + distance_to_end,
                distance_from_start=distance_from_start,
                distance_to_end=distance_to_end,
                position=position,
                parent=parent,
            )

            return state

        def get_node(position: Point, parent: PathFinderState | None):
            cached = state_cache.get(position, None)
            if cached is not None:
                return cached

            state = create_state(position, parent)
            state_cache[position] = state
            return state

        start_node = get_node(start, None)
        open_queue.add(start_node)

        global_closest = start_node

        while len(open_queue) > 0:
            current = open_queue.pop()
            current.closed = True

            if current.distance_to_end < global_closest.distance_to_end:
                global_closest = current

            if current.position == end:
                global_closest = current
                break

            room = self.map.rooms[current.position]

            for direction in Direction.get_directions():
                connection = room.get_connection(direction)
                if connection == NOT_CONNECTED:
                    continue

                neighbour_position = current.position + Point.from_direction(direction)
                neighbour = get_node(neighbour_position, current)

                if neighbour.closed:
                    continue

                new_distance_from_start = current.distance_from_start + 1

                if neighbour.heap_index == NOT_IN_HEAP or new_distance_from_start < neighbour.distance_from_start:
                    neighbour.distance_from_start = new_distance_from_start
                    neighbour.priority = neighbour.distance_from_start + neighbour.distance_to_end
                    neighbour.closed = False
                    neighbour.parent = current
                    open_queue.update_item(neighbour)

        end_time = perf_counter()
        print(f"Found path in {(end_time-start_time)*1000:.2f}ms")
        return global_closest.get_path()
