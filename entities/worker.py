import math
import random

import pygame

from config import WORKER_RADIUS
from entities.base_entity import BaseEntity


class Worker(BaseEntity):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, WORKER_RADIUS)
        self.speed = 1.7
        self.state = "IDLE"
        self.carrying_food = False
        self.carrying_resource = False
        self.repair_after_resource = False
        self.target_food = None
        self.food_target_x = None
        self.food_target_y = None
        self.target_resource = None
        self.resource_target_x = None
        self.resource_target_y = None

    def update(self, world, colony) -> None:
        if self.state == "IDLE":
            self.move_toward(world.nest_x, world.nest_y, self.speed * 0.25)
            self.apply_separation(colony.workers, self.radius * 2.4, 0.45, world)
            return

        if self.state == "MOVING_TO_RESOURCE":
            self._update_resource_trip(world, colony)
            return

        if self.state == "CARRYING_RESOURCE_HOME":
            self._return_resource_home(world, colony)
            return

        if self.state == "REPAIRING":
            self._repair_nest(world, colony)
            return

        if self.carrying_food:
            self.state = "CARRYING_FOOD_HOME"
            self.move_toward(world.nest_x, world.nest_y, self.speed)
            self.apply_separation(colony.workers, self.radius * 2.3, 0.4, world)
            if world.is_inside_nest(self.x, self.y):
                self.deposit_food(colony)
            return

        if self.state != "MOVING_TO_FOOD":
            self.state = "IDLE"
            return

        if self.target_food is None or self.target_food.is_empty():
            self.choose_food_target(world)

        if self.target_food is None:
            self.state = "IDLE"
            return

        self.move_toward(self.food_target_x, self.food_target_y, self.speed)
        self.apply_separation(colony.workers, self.radius * 2.4, 0.45, world)
        if self.distance_to(self.target_food.x, self.target_food.y) <= self.radius + self.target_food.size:
            self.collect_food()

    def choose_food_target(self, world) -> None:
        self.repair_after_resource = False
        self.target_food = world.get_nearest_food(self.x, self.y)
        if self.target_food:
            angle = random.uniform(0, math.tau)
            distance = random.uniform(self.target_food.size * 0.35, self.target_food.size * 1.25)
            self.food_target_x = self.target_food.x + math.cos(angle) * distance
            self.food_target_y = self.target_food.y + math.sin(angle) * distance
            self.state = "MOVING_TO_FOOD"
        else:
            self.food_target_x = None
            self.food_target_y = None
            self.state = "IDLE"

    def choose_resource_target(self, world, repair_after_resource: bool = False) -> None:
        self.repair_after_resource = repair_after_resource
        self.target_resource = world.get_nearest_resource(self.x, self.y)
        if self.target_resource:
            angle = random.uniform(0, math.tau)
            distance = random.uniform(self.target_resource.size * 0.35, self.target_resource.size * 1.25)
            self.resource_target_x = self.target_resource.x + math.cos(angle) * distance
            self.resource_target_y = self.target_resource.y + math.sin(angle) * distance
            self.state = "MOVING_TO_RESOURCE"
        else:
            self.resource_target_x = None
            self.resource_target_y = None
            self.repair_after_resource = False
            self.state = "IDLE"

    def collect_food(self) -> None:
        if self.target_food is None:
            return

        if self.target_food.take_food(1) > 0:
            self.carrying_food = True
            self.state = "CARRYING_FOOD_HOME"
        else:
            self.target_food = None
            self.food_target_x = None
            self.food_target_y = None
            self.state = "IDLE"

    def collect_resource(self) -> None:
        if self.target_resource is None:
            return

        if self.target_resource.take_resource(1) > 0:
            self.carrying_resource = True
            self.state = "CARRYING_RESOURCE_HOME"
        else:
            self.target_resource = None
            self.resource_target_x = None
            self.resource_target_y = None
            self.repair_after_resource = False
            self.state = "IDLE"

    def deposit_food(self, colony) -> None:
        if self.carrying_food:
            colony.deposit_food(1)
        self.carrying_food = False
        self.target_food = None
        self.food_target_x = None
        self.food_target_y = None
        self.state = "IDLE"

    def deposit_resource(self, colony) -> None:
        if self.carrying_resource:
            colony.deposit_resource(1)
        self.carrying_resource = False
        self.target_resource = None
        self.resource_target_x = None
        self.resource_target_y = None

        if self.repair_after_resource and colony.nest_health < colony.max_nest_health:
            self.state = "REPAIRING"
        else:
            self.repair_after_resource = False
            self.state = "IDLE"

    def _update_resource_trip(self, world, colony) -> None:
        if self.target_resource is None or self.target_resource.is_empty():
            self.choose_resource_target(world, self.repair_after_resource)

        if self.target_resource is None:
            self.state = "IDLE"
            return

        self.move_toward(self.resource_target_x, self.resource_target_y, self.speed)
        self.apply_separation(colony.workers, self.radius * 2.4, 0.45, world)
        if self.distance_to(self.target_resource.x, self.target_resource.y) <= self.radius + self.target_resource.size:
            self.collect_resource()

    def _return_resource_home(self, world, colony) -> None:
        self.move_toward(world.nest_x, world.nest_y, self.speed)
        self.apply_separation(colony.workers, self.radius * 2.3, 0.4, world)
        if world.is_inside_nest(self.x, self.y):
            self.deposit_resource(colony)

    def _repair_nest(self, world, colony) -> None:
        if colony.nest_health >= colony.max_nest_health:
            self.repair_after_resource = False
            self.state = "IDLE"
            return

        if colony.resource_storage <= 0:
            self.choose_resource_target(world, True)
            return

        self.move_toward(world.nest_x, world.nest_y, self.speed)
        self.apply_separation(colony.workers, self.radius * 2.2, 0.35, world)
        if world.is_inside_nest(self.x, self.y):
            if colony.consume_resource(1):
                colony.nest_health = min(colony.max_nest_health, colony.nest_health + 5)
            self.repair_after_resource = False
            self.state = "IDLE"

    def draw(self, surface) -> None:
        color = (15, 15, 15)
        if self.carrying_food:
            color = (25, 25, 25)
        elif self.carrying_resource:
            color = (35, 45, 55)

        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)
        if self.carrying_food:
            pygame.draw.circle(surface, (90, 210, 80), (int(self.x), int(self.y - 5)), 2)
        if self.carrying_resource:
            pygame.draw.circle(surface, (130, 165, 190), (int(self.x), int(self.y - 5)), 2)
