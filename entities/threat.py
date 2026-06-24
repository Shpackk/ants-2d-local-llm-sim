import math
import random

import pygame

from config import THREAT_RADIUS
from entities.base_entity import BaseEntity


class Threat(BaseEntity):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, THREAT_RADIUS)
        self.speed = 0.65
        self.state = "WANDERING"
        self.health = 40
        self.max_health = 40
        self.nest_attack_cooldown = 0
        self.worker_attack_cooldown = 0
        self.wander_target_x = None
        self.wander_target_y = None

    def update(self, world, colony) -> None:
        if self.health <= 0:
            self.is_alive = False
            return

        self.nest_attack_cooldown = max(0, self.nest_attack_cooldown - 1)
        self.worker_attack_cooldown = max(0, self.worker_attack_cooldown - 1)
        self._attack_workers(colony)

        if world.is_inside_nest(self.x, self.y):
            self.state = "ATTACKING_NEST"
            self._attack_nest(colony)
            return

        if self.distance_to(world.nest_x, world.nest_y) < world.nest_radius + 170:
            self.state = "MOVING_TO_NEST"
            self.move_toward(world.nest_x, world.nest_y, self.speed)
            return

        if self.wander_target_x is None or self.wander_target_y is None:
            self.choose_wander_target(world)

        self.state = "WANDERING"
        reached = self.move_toward(self.wander_target_x, self.wander_target_y, self.speed)
        if reached or self.distance_to(self.wander_target_x, self.wander_target_y) <= 5:
            self.choose_wander_target(world)

    def take_damage(self, amount: int) -> None:
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.is_alive = False

    def choose_wander_target(self, world) -> None:
        self.wander_target_x = random.uniform(self.radius, world.width - self.radius)
        self.wander_target_y = random.uniform(self.radius, world.height - self.radius)

    def _attack_nest(self, colony) -> None:
        if self.nest_attack_cooldown > 0:
            return

        colony.nest_health = max(0, colony.nest_health - 2)
        self.nest_attack_cooldown = 30

    def _attack_workers(self, colony) -> None:
        if self.worker_attack_cooldown > 0:
            return

        for worker in list(colony.workers):
            if self.distance_to(worker.x, worker.y) <= self.radius + worker.radius + 5:
                colony.workers.remove(worker)
                self.worker_attack_cooldown = 45
                return

    def draw(self, surface) -> None:
        points = [
            (int(self.x), int(self.y - self.radius)),
            (int(self.x - self.radius), int(self.y + self.radius)),
            (int(self.x + self.radius), int(self.y + self.radius)),
        ]
        pygame.draw.polygon(surface, (225, 115, 35), points)
        pygame.draw.polygon(surface, (115, 55, 15), points, 2)
        self._draw_healthbar(surface)

    def _draw_healthbar(self, surface) -> None:
        width = 26
        height = 4
        x = int(self.x - width / 2)
        y = int(self.y - self.radius - 10)
        ratio = self.health / self.max_health if self.max_health else 0
        pygame.draw.rect(surface, (60, 20, 20), (x, y, width, height))
        pygame.draw.rect(surface, (210, 45, 35), (x, y, int(width * ratio), height))
        pygame.draw.rect(surface, (30, 10, 10), (x, y, width, height), 1)
