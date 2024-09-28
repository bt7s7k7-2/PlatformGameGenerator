from pygame import Surface

from ..world.Actor import Actor


class GuiElement(Actor):
    def draw_gui(self, surface: Surface): ...

    def draw(self, surface: Surface):
        self.universe.queue_task(lambda: self.draw_gui(surface))
