from typing import TYPE_CHECKING, Callable, List

if TYPE_CHECKING:
    from ..generation.MapGenerator import MapGenerator
    from ..world.World import World

from .DependencyInjection import DependencyInjection


class Universe:
    world: "World | None" = None
    paused = False

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
