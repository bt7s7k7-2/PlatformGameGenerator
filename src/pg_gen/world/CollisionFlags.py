from enum import Flag, auto


class CollisionFlags(Flag):
    STATIC = auto()
    TRIGGER = auto()
