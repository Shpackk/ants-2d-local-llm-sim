import math
import random

from config import (
    NEST_RADIUS,
    NEST_X,
    NEST_Y,
    RANDOM_SEED,
    STARTING_FOOD_SOURCES,
    STARTING_RESOURCE_SOURCES,
    STARTING_THREATS,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)
from entities.food_source import FOOD_SOURCE_TYPES, FoodSource
from entities.resource_source import ResourceSource
from entities.threat import Threat


class World:
    def __init__(self) -> None:
        self.width = WORLD_WIDTH
        self.height = WORLD_HEIGHT
        self.nest_x = NEST_X
        self.nest_y = NEST_Y
        self.nest_radius = NEST_RADIUS
        self.food_sources = []
        self.resource_sources = []
        self.threats = []
        self.tick_count = 0

    def seed_world(self) -> None:
        random.seed(RANDOM_SEED)
        required_food_types = list(FOOD_SOURCE_TYPES.keys())
        food_types = required_food_types[:STARTING_FOOD_SOURCES]
        while len(food_types) < STARTING_FOOD_SOURCES:
            food_types.append(
                random.choices(
                    list(FOOD_SOURCE_TYPES.keys()),
                    weights=[0.45, 0.35, 0.20],
                    k=1,
                )[0]
            )
        random.shuffle(food_types)
        self.food_sources = [self._spawn_food_source(source_type) for source_type in food_types]
        self.resource_sources = [self._spawn_resource_source() for _ in range(STARTING_RESOURCE_SOURCES)]
        self.threats = [self._spawn_threat() for _ in range(STARTING_THREATS)]

    def update(self, colony) -> None:
        self.tick_count += 1
        for food_source in self.food_sources:
            food_source.update()
        for threat in self.threats:
            threat.update(self, colony)
        self.threats = [threat for threat in self.threats if threat.is_alive]

    def get_nearest_food(self, x: float, y: float):
        available_food = [food for food in self.food_sources if food.discovered and not food.is_empty()]
        if not available_food:
            return None
        return min(available_food, key=lambda food: math.hypot(food.x - x, food.y - y))

    def get_nearest_resource(self, x: float, y: float):
        available_resources = [resource for resource in self.resource_sources if not resource.is_empty()]
        if not available_resources:
            return None
        return min(available_resources, key=lambda resource: math.hypot(resource.x - x, resource.y - y))

    def get_priority_threat(self, x: float, y: float):
        if not self.threats:
            return None

        attacking = [threat for threat in self.threats if threat.state == "ATTACKING_NEST"]
        if attacking:
            return min(attacking, key=lambda threat: math.hypot(threat.x - x, threat.y - y))

        return min(self.threats, key=lambda threat: math.hypot(threat.x - x, threat.y - y))

    def known_food_sources(self) -> list[FoodSource]:
        return [food for food in self.food_sources if food.discovered]

    def hidden_food_sources(self) -> list[FoodSource]:
        return [food for food in self.food_sources if not food.discovered and not food.is_empty()]

    def is_inside_nest(self, x: float, y: float) -> bool:
        return math.hypot(self.nest_x - x, self.nest_y - y) <= self.nest_radius

    def draw(self, renderer, surface, colony) -> None:
        renderer.draw_world(surface, self, colony)

    def _spawn_food_source(self, source_type: str | None = None) -> FoodSource:
        x, y = self._random_position_away_from_nest(self.nest_radius + 120)
        if source_type is None:
            source_type = random.choices(
                list(FOOD_SOURCE_TYPES.keys()),
                weights=[0.45, 0.35, 0.20],
                k=1,
            )[0]
        config = FOOD_SOURCE_TYPES[source_type]
        amount = random.randint(config["min_amount"], config["max_amount"])
        return FoodSource(x, y, source_type, amount)

    def _spawn_resource_source(self) -> ResourceSource:
        x, y = self._random_position_away_from_nest(self.nest_radius + 100)
        return ResourceSource(x, y)

    def _spawn_threat(self) -> Threat:
        x, y = self._random_position_away_from_nest(self.nest_radius + 180)
        return Threat(x, y)

    def _random_position_away_from_nest(self, min_distance: float) -> tuple[float, float]:
        while True:
            x = random.uniform(40, self.width - 40)
            y = random.uniform(40, self.height - 40)
            if math.hypot(x - self.nest_x, y - self.nest_y) >= min_distance:
                return x, y
