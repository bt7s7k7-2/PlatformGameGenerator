from dataclasses import dataclass
from ...world.Actor import Actor


@dataclass
class GuiRenderer(Actor):

    def draw_gui(self): ...

    def draw(self):
        self.universe.queue_task(lambda: self.draw_gui())

        super().draw()
