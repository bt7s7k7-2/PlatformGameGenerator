import pygame
import pygame.freetype


class ResourceProvider:

    def __init__(self) -> None:
        self.font = pygame.freetype.SysFont("Arial", 12)
        pass

    __singleton_service__ = True
