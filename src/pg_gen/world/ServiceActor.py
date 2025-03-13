from dataclasses import dataclass
from typing import override

from .Actor import Actor


@dataclass
class ServiceActor(Actor):
    @override
    def on_created(self):
        self.universe.register_service_actor(self)
        return super().on_created()
