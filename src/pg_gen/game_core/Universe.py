from typing import TYPE_CHECKING, Callable, List

if TYPE_CHECKING:
    from ..world.ServiceActor import ServiceActor
    from ..generation.Map import Map
    from ..world.World import World

from .DependencyInjection import DependencyInjection


class Universe:
    map: "Map | None" = None

    @property
    def world(self):
        return self._world

    _world: "World | None" = None

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

        for actor in self._service_actors:
            actor.transfer_world(world)

    def execute_pending_tasks(self):
        while len(self._pending_tasks) > 0:
            tasks = self._pending_tasks
            self._pending_tasks = []
            for task in tasks:
                task()

    def register_service_actor(self, actor: "ServiceActor"):
        self._service_actors.append(actor)

    def queue_task(self, task: Callable[[], None]):
        self._pending_tasks.append(task)

    def __init__(self):
        self.di = DependencyInjection()
        self._pending_tasks: List[Callable[[], None]] = []
        self._service_actors: List["ServiceActor"] = []
        pass
