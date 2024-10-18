from typing import TYPE_CHECKING

from pygame import Surface

from .Camera import Camera

if TYPE_CHECKING:
    from .Universe import Universe


class GameLoop:
    def update_logic(self, delta_time: float):
        world = self.universe.world
        if world is not None:
            world.update(delta_time)

    def render_frame(self):
        self.surface.fill((0, 0, 0))

        world = self.universe.world
        if world is not None:
            world.draw()

    def update_and_render(self, delta_time: float):
        self.update_logic(delta_time)
        self.render_frame()

        self.universe.execute_pending_tasks()

    def __init__(self, surface: Surface, universe: "Universe") -> None:
        self.universe = universe
        self.surface = surface
        camera = Camera(screen=self.surface)
        self.universe.di.register(Camera, camera)
        pass
