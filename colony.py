import math
import random

from config import RANDOM_SEED, STARTING_WARRIORS, STARTING_WORKERS
from entities.queen import Queen
from entities.warrior import Warrior
from entities.worker import Worker


class Colony:
    def __init__(self) -> None:
        self.queen = None
        self.workers = []
        self.warriors = []
        self.food_storage = 0
        self.resource_storage = 0
        self.max_nest_health = 100
        self.nest_health = self.max_nest_health
        self.eggs = []
        self._last_world = None

    def seed_colony(self, world) -> None:
        random.seed(RANDOM_SEED + 1)
        self._last_world = world
        self.queen = Queen(world.nest_x, world.nest_y)
        self.workers = [Worker(*self._spawn_near_nest(world)) for _ in range(STARTING_WORKERS)]
        self.warriors = [Warrior(*self._spawn_near_nest(world)) for _ in range(STARTING_WARRIORS)]

    def update(self, world) -> None:
        self._last_world = world

        if self.queen:
            self.queen.update(world, self)

        for worker in list(self.workers):
            worker.update(world, self)

        for warrior in self.warriors:
            warrior.update(world, self)

        self._update_eggs(world)

    def deposit_food(self, amount: int) -> None:
        self.food_storage += amount

    def deposit_resource(self, amount: int) -> None:
        self.resource_storage += amount

    def consume_resource(self, amount: int) -> bool:
        if self.resource_storage < amount:
            return False
        self.resource_storage -= amount
        return True

    def get_state_summary(self, world) -> dict:
        workers_idle = sum(1 for worker in self.workers if worker.state == "IDLE")
        warriors_idle = sum(1 for warrior in self.warriors if warrior.state == "IDLE")
        threats_attacking_nest = sum(1 for threat in world.threats if threat.state == "ATTACKING_NEST")
        resources_available = sum(resource.amount for resource in world.resource_sources)

        return {
            "food_storage": self.food_storage,
            "resource_storage": self.resource_storage,
            "resources_available": resources_available,
            "workers_total": len(self.workers),
            "workers_idle": workers_idle,
            "warriors_total": len(self.warriors),
            "warriors_idle": warriors_idle,
            "active_threats": len(world.threats),
            "threats_attacking_nest": threats_attacking_nest,
            "nest_health": self.nest_health,
        }

    def execute_queen_command(self, command: dict) -> None:
        action = command["action"]
        amount = command["amount"]

        print(f"[Queen Command] {command}")

        if action == "assign_workers_to_food":
            self.assign_workers_to_food(amount)
        elif action == "assign_workers_to_repair":
            self.assign_workers_to_repair(amount)
        elif action == "assign_warriors_to_guard":
            self.assign_warriors_to_guard(amount)
        elif action == "remove_threats":
            self.remove_threats(amount)
        elif action == "lay_worker_eggs":
            self.lay_eggs("worker", amount)
        elif action == "lay_warrior_eggs":
            self.lay_eggs("warrior", amount)
        elif action == "do_nothing":
            pass

    def assign_workers_to_food(self, amount: int) -> None:
        assigned = 0

        for worker in self.workers:
            if assigned >= amount:
                break

            if worker.state == "IDLE":
                worker.state = "MOVING_TO_FOOD"
                worker.choose_food_target(self._last_world)
                assigned += 1

    def assign_workers_to_repair(self, amount: int) -> None:
        assigned = 0

        for worker in self.workers:
            if assigned >= amount:
                break

            if worker.state == "IDLE":
                if self.resource_storage > 0:
                    worker.state = "REPAIRING"
                else:
                    worker.choose_resource_target(self._last_world, True)
                assigned += 1

    def assign_warriors_to_guard(self, amount: int) -> None:
        assigned = 0

        for warrior in self.warriors:
            if assigned >= amount:
                break

            if warrior.state == "IDLE":
                warrior.choose_guard_position(self._last_world)
                assigned += 1

    def remove_threats(self, amount: int) -> None:
        assigned = 0

        for warrior in self.warriors:
            if assigned >= amount:
                break

            if warrior.state in ("IDLE", "GUARDING"):
                warrior.choose_threat_target(self._last_world)
                assigned += 1

    def lay_eggs(self, ant_type: str, amount: int) -> None:
        food_cost_per_egg = 10
        total_cost = amount * food_cost_per_egg

        if self.food_storage < total_cost:
            amount = self.food_storage // food_cost_per_egg
            total_cost = amount * food_cost_per_egg

        if amount <= 0:
            return

        self.food_storage -= total_cost

        for _ in range(amount):
            self.eggs.append(
                {
                    "type": ant_type,
                    "ticks_until_hatch": 600,
                }
            )

    def get_worker_count(self) -> int:
        return len(self.workers)

    def get_warrior_count(self) -> int:
        return len(self.warriors)

    def workers_carrying_food(self) -> int:
        return sum(1 for worker in self.workers if worker.carrying_food)

    def workers_carrying_resources(self) -> int:
        return sum(1 for worker in self.workers if worker.carrying_resource)

    def _spawn_near_nest(self, world) -> tuple[float, float]:
        angle = random.uniform(0, math.tau)
        distance = random.uniform(10, world.nest_radius - 5)
        x = world.nest_x + math.cos(angle) * distance
        y = world.nest_y + math.sin(angle) * distance
        return x, y

    def _update_eggs(self, world) -> None:
        hatched_eggs = []

        for egg in self.eggs:
            egg["ticks_until_hatch"] -= 1
            if egg["ticks_until_hatch"] <= 0:
                hatched_eggs.append(egg)

        self.eggs = [egg for egg in self.eggs if egg["ticks_until_hatch"] > 0]

        for egg in hatched_eggs:
            x, y = self._spawn_near_nest(world)
            if egg["type"] == "warrior":
                self.warriors.append(Warrior(x, y))
            else:
                self.workers.append(Worker(x, y))
