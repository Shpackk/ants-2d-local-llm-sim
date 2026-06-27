import math
import random

from config import (
    ANT_FOOD_CONSUMPTION_TICKS,
    COLONY_TARGET_ANTS,
    EGG_HATCH_TICKS,
    EXPLORATION_RECALL_TICKS,
    FOOD_COST_PER_EGG,
    RANDOM_SEED,
    STARTING_FOOD_STORAGE,
    STARTING_WARRIORS,
    STARTING_WORKERS,
)
from entities.queen import Queen
from entities.warrior import Warrior
from entities.worker import Worker


MAX_QUEEN_COMMAND_QUEUE = 16


class Colony:
    def __init__(self) -> None:
        self.queen = None
        self.workers = []
        self.warriors = []
        self.food_storage = STARTING_FOOD_STORAGE
        self.resource_storage = 0
        self.max_nest_health = 100
        self.nest_health = self.max_nest_health
        self.eggs = []
        self.deaths = 0
        self.goal_reached = False
        self.lost = False
        self.loss_reason = None
        self.queen_command_queue = []
        self._last_world = None
        self._food_consumption_progress = 0.0

    def seed_colony(self, world) -> None:
        random.seed(RANDOM_SEED + 1)
        self._last_world = world
        self.queen = Queen(world.nest_x, world.nest_y)
        self.workers = [Worker(*self._spawn_near_nest(world)) for _ in range(STARTING_WORKERS)]
        self.warriors = [Warrior(*self._spawn_near_nest(world)) for _ in range(STARTING_WARRIORS)]

    def update(self, world) -> None:
        if self.goal_reached or self.lost:
            return

        self._last_world = world
        self._process_queen_command_queue()

        if self.queen:
            self.queen.update(world, self)

        for worker in list(self.workers):
            worker.update(world, self)

        for warrior in self.warriors:
            warrior.update(world, self)

        self._update_eggs(world)
        self._consume_food()
        self._update_outcome(world)

    def deposit_food(self, amount: int) -> None:
        self.food_storage += amount

    def deposit_resource(self, amount: int) -> None:
        self.resource_storage += amount

    def consume_resource(self, amount: int) -> bool:
        if self.resource_storage < amount:
            return False
        self.resource_storage -= amount
        return True

    def living_ant_count(self) -> int:
        queen_count = 1 if self.queen else 0
        return queen_count + len(self.workers) + len(self.warriors)

    def get_state_summary(self, world) -> dict:
        workers_idle = sum(1 for worker in self.workers if worker.state == "IDLE")
        workers_exploring = sum(1 for worker in self.workers if worker.state == "EXPLORING")
        workers_exploring_too_long = sum(
            1
            for worker in self.workers
            if worker.state == "EXPLORING" and worker.exploration_ticks >= EXPLORATION_RECALL_TICKS
        )
        workers_foraging = sum(1 for worker in self.workers if worker.state in ("MOVING_TO_FOOD", "CARRYING_FOOD_HOME"))
        workers_returning_with_food = sum(1 for worker in self.workers if worker.carrying_food)
        food_in_transit = sum(worker.carrying_food_amount for worker in self.workers if worker.carrying_food)
        workers_available_for_food = workers_idle + workers_foraging
        warriors_idle = sum(1 for warrior in self.warriors if warrior.state == "IDLE")
        threats_attacking_nest = sum(1 for threat in world.threats if threat.state == "ATTACKING_NEST")
        resources_available = sum(resource.amount for resource in world.resource_sources)
        known_food = world.known_food_sources()
        known_food_available = [food for food in known_food if not food.is_empty()]
        known_food_details = [
            {
                "type": food.source_type,
                "amount": food.amount,
                "capacity": food.max_amount,
                "carry_yield": food.carry_yield,
                "regen_ticks": food.regen_ticks,
                "reserve_ratio": round(food.reserve_ratio(), 2),
                "depleted": food.is_empty(),
            }
            for food in known_food
        ]
        living_ants = self.living_ant_count()
        eggs_count = len(self.eggs)
        ants_needed = max(0, COLONY_TARGET_ANTS - living_ants)
        ants_needed_after_current_eggs = max(0, COLONY_TARGET_ANTS - living_ants - eggs_count)
        food_needed_for_missing_eggs = ants_needed_after_current_eggs * FOOD_COST_PER_EGG
        food_reserve_for_hatch_window = math.ceil(living_ants * EGG_HATCH_TICKS / ANT_FOOD_CONSUMPTION_TICKS)
        egg_affordable_after_reserve = max(0, (self.food_storage - food_reserve_for_hatch_window) // FOOD_COST_PER_EGG)
        stored_food_after_missing_eggs = self.food_storage - food_needed_for_missing_eggs
        food_buffer_ticks_without_new_food = (
            int(((self.food_storage + food_in_transit) * ANT_FOOD_CONSUMPTION_TICKS) / living_ants)
            if living_ants > 0
            else 0
        )

        return {
            "tick": world.tick_count,
            "goal": f"reach {COLONY_TARGET_ANTS} living ants",
            "goal_reached": self.goal_reached,
            "lost": self.lost,
            "loss_reason": self.loss_reason,
            "living_ants": living_ants,
            "target_ants": COLONY_TARGET_ANTS,
            "ants_needed": ants_needed,
            "eggs_needed_after_current_eggs": ants_needed_after_current_eggs,
            "food_needed_for_missing_eggs": food_needed_for_missing_eggs,
            "max_eggs_affordable_from_storage": self.food_storage // FOOD_COST_PER_EGG,
            "food_reserve_for_hatch_window": food_reserve_for_hatch_window,
            "egg_affordable_after_reserve": egg_affordable_after_reserve,
            "stored_food_after_missing_eggs": stored_food_after_missing_eggs,
            "food_buffer_ticks_without_new_food": food_buffer_ticks_without_new_food,
            "queen_alive": self.queen is not None,
            "food_storage": self.food_storage,
            "food_in_transit": food_in_transit,
            "resource_storage": self.resource_storage,
            "resources_available": resources_available,
            "workers_total": len(self.workers),
            "workers_idle": workers_idle,
            "workers_exploring": workers_exploring,
            "workers_exploring_too_long": workers_exploring_too_long,
            "exploration_recall_ticks": EXPLORATION_RECALL_TICKS,
            "workers_foraging": workers_foraging,
            "workers_returning_with_food": workers_returning_with_food,
            "workers_available_for_food": workers_available_for_food,
            "warriors_total": len(self.warriors),
            "warriors_idle": warriors_idle,
            "eggs": len(self.eggs),
            "egg_hatch_ticks": EGG_HATCH_TICKS,
            "food_cost_per_egg": FOOD_COST_PER_EGG,
            "known_food_sources": len(known_food),
            "known_food_available_sources": len(known_food_available),
            "known_food_depleted_sources": len(known_food) - len(known_food_available),
            "known_food_remaining": sum(food.amount for food in known_food_available),
            "known_food_capacity": sum(food.max_amount for food in known_food),
            "known_food_average_reserve_ratio": round(
                sum(food.reserve_ratio() for food in known_food_available) / len(known_food_available),
                2,
            )
            if known_food_available
            else 0.0,
            "known_food_details": known_food_details,
            "active_threats": len(world.threats),
            "threats_attacking_nest": threats_attacking_nest,
            "nest_health": self.nest_health,
            "deaths": self.deaths,
        }

    def execute_queen_command(self, command: dict) -> None:
        if "commands" in command:
            print(f"[Queen Commands] {command}")
            for single_command in command["commands"]:
                self._execute_or_queue_queen_command(single_command)
            return

        self._execute_or_queue_queen_command(command)

    def _process_queen_command_queue(self) -> None:
        if not self.queen_command_queue:
            return

        queued_commands = self.queen_command_queue
        self.queen_command_queue = []
        for command in queued_commands:
            self._execute_or_queue_queen_command(command, from_queue=True)

    def _execute_or_queue_queen_command(self, command: dict, from_queue: bool = False) -> None:
        action = command["action"]
        amount = command["amount"]

        completed_amount = self._execute_single_queen_command(action, amount)
        if not from_queue or completed_amount > 0:
            print(f"[Queen Command] {command}")

        if action == "do_nothing" or completed_amount >= amount:
            return

        if len(self.queen_command_queue) >= MAX_QUEEN_COMMAND_QUEUE:
            return

        remaining_command = {
            **command,
            "amount": amount - completed_amount if completed_amount > 0 else amount,
        }
        if remaining_command not in self.queen_command_queue:
            self.queen_command_queue.append(remaining_command)

    def _execute_single_queen_command(self, action: str, amount: int) -> int:
        if action == "assign_workers_to_explore":
            return self.assign_workers_to_explore(amount)
        elif action == "recall_long_explorers":
            return self.recall_long_explorers(amount)
        elif action == "assign_workers_to_food":
            return self.assign_workers_to_food(amount)
        elif action == "assign_workers_to_repair":
            return self.assign_workers_to_repair(amount)
        elif action == "assign_warriors_to_guard":
            return self.assign_warriors_to_guard(amount)
        elif action == "remove_threats":
            return self.remove_threats(amount)
        elif action == "lay_worker_eggs":
            return self.lay_eggs("worker", amount)
        elif action == "lay_warrior_eggs":
            return self.lay_eggs("warrior", amount)
        elif action == "do_nothing":
            return amount

        return 0

    def assign_workers_to_explore(self, amount: int) -> int:
        assigned = 0

        for worker in self.workers:
            if assigned >= amount:
                break

            if worker.state == "IDLE":
                worker.choose_explore_target(self._last_world)
                assigned += 1

        return assigned

    def recall_long_explorers(self, amount: int) -> int:
        recalled = 0
        explorers = [
            worker
            for worker in self.workers
            if worker.state == "EXPLORING" and worker.exploration_ticks >= EXPLORATION_RECALL_TICKS
        ]
        explorers.sort(key=lambda worker: worker.exploration_ticks, reverse=True)

        for worker in explorers:
            if recalled >= amount:
                break

            worker.recall_from_exploration()
            recalled += 1

        return recalled

    def assign_workers_to_food(self, amount: int) -> int:
        desired_foragers = min(amount, len(self.workers))
        queued_or_active = 0

        for worker in self.workers:
            if queued_or_active >= desired_foragers:
                break

            if worker.carrying_food:
                worker.continue_foraging_after_dropoff = True
                queued_or_active += 1
            elif worker.state == "MOVING_TO_FOOD":
                queued_or_active += 1

        for worker in self.workers:
            if queued_or_active >= desired_foragers:
                break

            if worker.state == "IDLE":
                worker.choose_food_target(self._last_world)
                queued_or_active += 1

        return queued_or_active

    def assign_workers_to_repair(self, amount: int) -> int:
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

        return assigned

    def assign_warriors_to_guard(self, amount: int) -> int:
        assigned = 0

        for warrior in self.warriors:
            if assigned >= amount:
                break

            if warrior.state == "IDLE":
                warrior.choose_guard_position(self._last_world)
                assigned += 1

        return assigned

    def remove_threats(self, amount: int) -> int:
        assigned = 0

        for warrior in self.warriors:
            if assigned >= amount:
                break

            if warrior.state in ("IDLE", "GUARDING"):
                warrior.choose_threat_target(self._last_world)
                assigned += 1

        return assigned

    def lay_eggs(self, ant_type: str, amount: int) -> int:
        total_cost = amount * FOOD_COST_PER_EGG

        if self.food_storage < total_cost:
            amount = self.food_storage // FOOD_COST_PER_EGG
            total_cost = amount * FOOD_COST_PER_EGG

        if amount <= 0:
            return 0

        self.food_storage -= total_cost

        for _ in range(amount):
            self.eggs.append(
                {
                    "type": ant_type,
                    "ticks_until_hatch": EGG_HATCH_TICKS,
                }
            )

        return amount

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

    def _consume_food(self) -> None:
        self._food_consumption_progress += self.living_ant_count() / ANT_FOOD_CONSUMPTION_TICKS
        food_needed = int(self._food_consumption_progress)

        if food_needed <= 0:
            return

        self._food_consumption_progress -= food_needed

        for _ in range(food_needed):
            if self.food_storage > 0:
                self.food_storage -= 1
            else:
                self._starve_one_ant()

    def _starve_one_ant(self) -> None:
        if self.workers:
            self.workers.pop()
            self.deaths += 1
            return

        if self.warriors:
            self.warriors.pop()
            self.deaths += 1
            return

        if self.queen:
            self.queen = None
            self.deaths += 1

    def _update_outcome(self, world) -> None:
        if self.living_ant_count() >= COLONY_TARGET_ANTS:
            self.goal_reached = True
            print(f"[Goal] Reached {COLONY_TARGET_ANTS} living ants at tick {world.tick_count}")
            return

        if self.queen is None:
            self.lost = True
            self.loss_reason = "queen died"
        elif not self.workers and not self.eggs:
            self.lost = True
            self.loss_reason = "no workers or eggs left"
