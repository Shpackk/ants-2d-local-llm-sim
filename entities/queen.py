import math

import pygame

from config import QUEEN_RADIUS
from entities.base_entity import BaseEntity


class Queen(BaseEntity):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, QUEEN_RADIUS)
        self.health = 100
        self.state = "IDLE"
        self.pulse_timer = 0.0

    def update(self, world, colony) -> None:
        self.pulse_timer += 0.05

    def draw(self, surface) -> None:
        pulse = int(math.sin(self.pulse_timer) * 2)
        pygame.draw.circle(
            surface,
            (140, 75, 190),
            (int(self.x), int(self.y)),
            self.radius + pulse,
        )
        pygame.draw.circle(
            surface,
            (70, 30, 105),
            (int(self.x), int(self.y)),
            self.radius + pulse,
            2,
        )
