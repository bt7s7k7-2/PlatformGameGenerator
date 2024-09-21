from enum import IntEnum


class Direction(IntEnum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

    @staticmethod
    def get_directions():
        return [Direction.UP, Direction.RIGHT, Direction.DOWN, Direction.LEFT]

    def invert(self):
        return Direction((self + 2) % 4)
