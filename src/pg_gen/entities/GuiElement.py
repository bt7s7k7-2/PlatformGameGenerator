from ..world.Actor import Actor


class GuiElement(Actor):
    def draw_gui(self): ...

    def draw(self):
        self.universe.queue_task(lambda: self.draw_gui())
