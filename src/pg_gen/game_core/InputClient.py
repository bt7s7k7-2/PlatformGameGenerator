from functools import cached_property

from ..world.Actor import Actor
from .InputState import InputState


class InputClient(Actor):
    @cached_property
    def _input(self):
        return self.universe.di.inject(InputState)
