from typing import TYPE_CHECKING, Callable, List

if TYPE_CHECKING:
    from ..generation.MapGenerator import MapGenerator
    from ..world.World import World

from .DependencyInjection import DependencyInjection


class Universe:

    @property
    def world(self):
        return self._world

    _world: "World | None" = None
    paused = False

    def set_world(self, world: "World"):
        if self.world == world:
            return

        if self._world is not None:
            self._world.active = False
            for actor in self._world.get_actors():
                actor.on_removed()

        self._world = world

        world.active = True
        for actor in world.get_actors():
            actor.on_added()

    def execute_pending_tasks(self):
        while len(self._pending_tasks) > 0:
            tasks = self._pending_tasks
            self._pending_tasks = []
            for task in tasks:
                task()

    def queue_task(self, task: Callable[[], None]):
        self._pending_tasks.append(task)

    def __init__(self, map: "MapGenerator | None"):
        self.di = DependencyInjection()
        self.map = map
        self._pending_tasks: List[Callable[[], None]] = []
        pass
