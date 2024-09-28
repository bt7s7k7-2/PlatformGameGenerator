from typing import List

import pygame


class InputState:
    left = False
    right = False
    jump = False
    up = False
    down = False

    keys: pygame.key.ScancodeWrapper = None # type: ignore

    __singleton_service__ = True

    def __init__(self) -> None:
        self.events: List[pygame.event.Event] = []
        pass
