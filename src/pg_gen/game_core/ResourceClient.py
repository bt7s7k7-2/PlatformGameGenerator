from functools import cached_property

from ..world.Actor import Actor
from .ResourceProvider import ResourceProvider


class ResourceClient(Actor):
    @cached_property
    def _resource_provider(self):
        return self.universe.di.inject(ResourceProvider)
