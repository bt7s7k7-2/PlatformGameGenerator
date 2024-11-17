from dataclasses import dataclass

from ...world.Actor import Actor


@dataclass
class ConfigurableObject(Actor):
    config: str = ""

    def apply_config(self, config: str) -> bool:
        self.config = config
        return True
