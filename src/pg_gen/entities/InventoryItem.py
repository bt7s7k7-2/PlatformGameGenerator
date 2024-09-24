from dataclasses import dataclass, field

from ..world.Actor import Actor
from ..world.SpriteLayer import SpriteLayer


@dataclass
class InventoryItem(Actor):
    layer: SpriteLayer = field(default=SpriteLayer.GUI)
