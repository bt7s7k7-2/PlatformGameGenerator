from dataclasses import dataclass
from typing import override

from ...world.Actor import Actor


@dataclass
class GuiRenderer(Actor):

    def draw_gui(self): ...

    @override
    def draw(self):
        self.universe.queue_task(lambda: self.draw_gui())

        super().draw()
