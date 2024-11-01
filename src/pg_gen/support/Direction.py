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

    @property
    def horizontal(self):
        return self == Direction.RIGHT or self == Direction.LEFT

    def flipX(self, flip=True):
        if not flip:
            return self
        if self.horizontal:
            return self.invert()
        return self
