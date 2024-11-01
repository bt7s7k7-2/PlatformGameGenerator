from dataclasses import dataclass

from .Actor import Actor


@dataclass
class ServiceActor(Actor):
    def on_created(self):
        self.universe.register_service_actor(self)
        return super().on_created()
