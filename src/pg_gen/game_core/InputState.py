import pygame


class InputState:
    left = False
    right = False
    jump = False
    up = False
    down = False

    keys: pygame.key.ScancodeWrapper = None  # type: ignore

    __singleton_service__ = True

    def clear(self):
        self.events.clear()
        self.left = False
        self.right = False
        self.jump = False
        self.up = False
        self.down = False

    def __init__(self) -> None:
        self.events: list[pygame.event.Event] = []
        pass
