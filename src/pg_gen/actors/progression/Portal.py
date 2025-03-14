from dataclasses import dataclass, field
from math import pi, sin
from typing import override

from pg_gen.generation.RoomInfo import RoomInfo

from ...game_core.Camera import CameraClient
from ...game_core.ResourceClient import ResourceClient
from ...generation.RoomInfo import ALTAR
from ...level_editor.ActorRegistry import ActorRegistry
from ...support.Color import Color
from ...support.Point import Point
from ...world.Actor import Actor
from ...world.CollisionFlags import CollisionFlags
from ...world.SpriteLayer import SpriteLayer
from ..Player import Player
from ..support.PersistentObject import PersistentObject
from .Key import KeyItem


@dataclass(kw_only=True)
class PortalEyeAnimation(ResourceClient, CameraClient, Actor):
    start_pos: Point
    end_pos: Point
    portal: "Portal"
    time = 0.0
    player: Player

    @override
    def update(self, delta: float):
        self.time += delta
        self.position = self.start_pos.lerp(self.end_pos, self.time)
        if self.time > 1:
            self.universe.queue_task(lambda: self.remove())
            self.portal.persistent_value += 1
            self.time = 1
            self.player.score += 50
        self.size = Point.ONE * float(sin(self.time * pi) ** 0.5)

    @override
    def draw(self):
        sprite = self._resource_provider.eye_sprite
        self._camera.draw_texture(self.position - self.size * 0.5, self.size, sprite)


@dataclass
class Portal(ResourceClient, CameraClient, PersistentObject[int], Actor):
    collision_flags: CollisionFlags = field(default=CollisionFlags.TRIGGER)
    layer: SpriteLayer = field(default=SpriteLayer.BACKGROUND)
    size: Point = field(default=Point(3, 3))
    sprite: str = ""
    slide_only: bool = False
    time = 0.0
    required_eyes = 1

    @property
    def is_open(self):
        return self.persistent_value >= self.required_eyes

    @override
    def _get_default_persistent_value(self):
        return 0

    @override
    def init_persistent_object(self, room: RoomInfo, flag_index: int):
        super().init_persistent_object(room, flag_index)
        if self.universe.map:
            self.required_eyes = len(self.universe.map.altars)

    @override
    def update(self, delta: float):
        self.time += delta
        if not self.is_open and self.time > 0.1:
            player = self.universe.di.try_inject(Player)
            if player is None:
                return
            player_center = player.position + player.size * 0.5
            self_center = self.position + self.size * 0.5
            distance = Point.distance(player_center, self_center)
            if distance > 5:
                return
            eye = player.take_inventory_item(lambda v: isinstance(v, KeyItem) and v.key_type == ALTAR)
            if eye is None:
                return

            self.world.add_actor(
                PortalEyeAnimation(
                    start_pos=player_center,
                    end_pos=self_center,
                    portal=self,
                    player=player,
                )
            )
            self.time = 0

    @override
    def draw(self):
        if self.is_open:
            sprite = self._resource_provider.portal[int(self.time * 6) % len(self._resource_provider.portal)]
        else:
            sprite = self._resource_provider.empty_portal

            self._resource_provider.display_font.render_to(
                self._camera.screen,
                self._camera.world_to_screen(self.position + Point(1.2, 1.33)).to_pygame_rect(Point.ONE * self._camera.zoom),
                text=f"{self.required_eyes - self.persistent_value}",
                fgcolor=Color.YELLOW.to_pygame_color(),
            )

        self._camera.draw_texture(self.position, self.size, sprite)

    @override
    def on_trigger(self, trigger: Actor):
        if self.is_open and isinstance(trigger, Player):
            trigger.game_over()


ActorRegistry.register_actor(Portal)
