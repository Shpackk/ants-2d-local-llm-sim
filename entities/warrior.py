import math
import random

import pygame

from config import WARRIOR_RADIUS
from entities.base_entity import BaseEntity


class Warrior(BaseEntity):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, WARRIOR_RADIUS)
        self.speed = 1.35
        self.state = "IDLE"
        self.attack_damage = 4
        self.attack_cooldown = 0
        self.target_threat = None
        self.patrol_target_x = None
        self.patrol_target_y = None
        self.guard_target_x = None
        self.guard_target_y = None

    def update(self, world, colony) -> None:
        self.attack_cooldown = max(0, self.attack_cooldown - 1)

        if self.state == "ATTACKING_THREAT":
            self._attack_threat(world, colony)
            return

        if self.state == "GUARDING":
            if self.guard_target_x is None or self.guard_target_y is None:
                self.choose_guard_position(world)
            self.move_toward(self.guard_target_x, self.guard_target_y, self.speed)
            self.apply_separation(colony.warriors, self.radius * 2.4, 0.45, world)
            return

        if self.state == "IDLE":
            self.apply_separation(colony.warriors, self.radius * 2.1, 0.25, world)
            return

        if self.patrol_target_x is None or self.patrol_target_y is None:
            self.choose_patrol_target(world)

        reached = self.move_toward(self.patrol_target_x, self.patrol_target_y, self.speed)
        self.apply_separation(colony.warriors, self.radius * 2.2, 0.3, world)
        if reached or self.distance_to(self.patrol_target_x, self.patrol_target_y) <= 4:
            self.state = "IDLE"
            self.patrol_target_x = None
            self.patrol_target_y = None

    def choose_guard_position(self, world) -> None:
        self.state = "GUARDING"
        angle = random.uniform(0, math.tau)
        distance = random.uniform(world.nest_radius + 12, world.nest_radius + 42)
        self.guard_target_x = max(self.radius, min(world.width - self.radius, world.nest_x + math.cos(angle) * distance))
        self.guard_target_y = max(self.radius, min(world.height - self.radius, world.nest_y + math.sin(angle) * distance))

    def choose_patrol_target(self, world) -> None:
        self.state = "PATROLLING"
        angle = random.uniform(0, math.tau)
        distance = random.uniform(80, 180)
        self.patrol_target_x = max(0, min(world.width, world.nest_x + math.cos(angle) * distance))
        self.patrol_target_y = max(0, min(world.height, world.nest_y + math.sin(angle) * distance))

    def choose_threat_target(self, world) -> None:
        self.target_threat = world.get_priority_threat(self.x, self.y)
        if self.target_threat is None:
            self.state = "IDLE"
        else:
            self.state = "ATTACKING_THREAT"

    def _attack_threat(self, world, colony) -> None:
        if self.target_threat is None or not self.target_threat.is_alive:
            self.choose_threat_target(world)

        if self.target_threat is None:
            return

        self.move_toward(self.target_threat.x, self.target_threat.y, self.speed * 1.25)
        self.apply_separation(colony.warriors, self.radius * 2.2, 0.3, world)
        if self.distance_to(self.target_threat.x, self.target_threat.y) <= self.radius + self.target_threat.radius + 4:
            if self.attack_cooldown <= 0:
                self.target_threat.take_damage(self.attack_damage)
                self.attack_cooldown = 15

            if not self.target_threat.is_alive:
                self.target_threat = None
                self.choose_threat_target(world)

    def draw(self, surface) -> None:
        pygame.draw.circle(surface, (190, 35, 35), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (90, 15, 15), (int(self.x), int(self.y)), self.radius, 1)
