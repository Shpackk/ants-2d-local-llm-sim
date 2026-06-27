import json
from datetime import datetime
from pathlib import Path

from config import (
    ANT_FOOD_CONSUMPTION_TICKS,
    COLONY_TARGET_ANTS,
    EGG_HATCH_TICKS,
    FOOD_COST_PER_EGG,
    MAX_SIMULATION_TICKS,
    RANDOM_SEED,
    STARTING_FOOD_SOURCES,
    STARTING_FOOD_STORAGE,
    STARTING_RESOURCE_SOURCES,
    STARTING_THREATS,
    STARTING_WARRIORS,
    STARTING_WORKERS,
)


class GameStatsRecorder:
    def __init__(self, model_name: str, sample_interval_ticks: int = 500, output_dir: str = "stats") -> None:
        self.model_name = model_name
        self.sample_interval_ticks = sample_interval_ticks
        self.output_dir = Path(output_dir)
        self.samples = []
        self.queen_commands = []
        self._sampled_ticks = set()
        self._saved_path = None

    def record_if_due(self, world, colony) -> None:
        if world.tick_count % self.sample_interval_ticks == 0:
            self.record_snapshot(world, colony)

    def record_snapshot(self, world, colony) -> None:
        if world.tick_count in self._sampled_ticks:
            return

        self.samples.append(self._build_snapshot(world, colony))
        self._sampled_ticks.add(world.tick_count)

    def record_queen_command(self, tick: int, command: dict) -> None:
        self.queen_commands.append(
            {
                "tick": tick,
                "command": command,
            }
        )

    def save(self, world, colony) -> Path:
        if self._saved_path is not None:
            return self._saved_path

        self.record_snapshot(world, colony)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        outcome = "win" if colony.goal_reached else "loss" if colony.lost else "unfinished"
        output_path = self.output_dir / f"game_stats_{timestamp}_{outcome}.json"
        output_path.write_text(json.dumps(self._build_report(world, colony), indent=2), encoding="utf-8")
        self._saved_path = output_path
        return output_path

    def _build_report(self, world, colony) -> dict:
        return {
            "model_name": self.model_name,
            "metadata": {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "model_name": self.model_name,
                "sample_interval_ticks": self.sample_interval_ticks,
                "random_seed": RANDOM_SEED,
                "config": {
                    "starting_workers": STARTING_WORKERS,
                    "starting_warriors": STARTING_WARRIORS,
                    "starting_food_storage": STARTING_FOOD_STORAGE,
                    "starting_food_sources": STARTING_FOOD_SOURCES,
                    "starting_resource_sources": STARTING_RESOURCE_SOURCES,
                    "starting_threats": STARTING_THREATS,
                    "target_ants": COLONY_TARGET_ANTS,
                    "food_cost_per_egg": FOOD_COST_PER_EGG,
                    "egg_hatch_ticks": EGG_HATCH_TICKS,
                    "ant_food_consumption_ticks": ANT_FOOD_CONSUMPTION_TICKS,
                    "max_simulation_ticks": MAX_SIMULATION_TICKS,
                },
            },
            "outcome": {
                "result": "win" if colony.goal_reached else "loss" if colony.lost else "unfinished",
                "tick": world.tick_count,
                "goal_reached": colony.goal_reached,
                "lost": colony.lost,
                "loss_reason": colony.loss_reason,
            },
            "summary": self._build_snapshot(world, colony),
            "queen_commands": self.queen_commands,
            "samples": self.samples,
        }

    def _build_snapshot(self, world, colony) -> dict:
        state = colony.get_state_summary(world)
        food_sources = self._food_source_details(world)
        resource_sources = self._resource_source_details(world)
        all_food_remaining = sum(food["amount"] for food in food_sources)
        all_food_capacity = sum(food["capacity"] for food in food_sources)
        map_food_available_sources = sum(1 for food in food_sources if not food["depleted"])
        discovered_food_sources = sum(1 for food in food_sources if food["discovered"])

        return {
            **state,
            "map_food_remaining": all_food_remaining,
            "map_food_capacity": all_food_capacity,
            "map_food_available_sources": map_food_available_sources,
            "map_food_depleted_sources": len(food_sources) - map_food_available_sources,
            "map_food_sources": len(food_sources),
            "hidden_food_sources": len(food_sources) - discovered_food_sources,
            "llm_found_food_sources": discovered_food_sources,
            "queen_command_count": len(self.queen_commands),
            "queen_action_counts": self._queen_action_counts(),
            "food_sources": food_sources,
            "resource_sources": resource_sources,
        }

    def _food_source_details(self, world) -> list[dict]:
        return [
            {
                "id": index,
                "type": food.source_type,
                "x": round(food.x, 2),
                "y": round(food.y, 2),
                "amount": food.amount,
                "capacity": food.max_amount,
                "carry_yield": food.carry_yield,
                "regen_ticks": food.regen_ticks,
                "reserve_ratio": round(food.reserve_ratio(), 4),
                "discovered": food.discovered,
                "depleted": food.is_empty(),
            }
            for index, food in enumerate(world.food_sources)
        ]

    def _resource_source_details(self, world) -> list[dict]:
        return [
            {
                "id": index,
                "x": round(resource.x, 2),
                "y": round(resource.y, 2),
                "amount": resource.amount,
                "capacity": resource.max_amount,
                "depleted": resource.is_empty(),
            }
            for index, resource in enumerate(world.resource_sources)
        ]

    def _queen_action_counts(self) -> dict:
        action_counts = {}
        for entry in self.queen_commands:
            for command in self._iter_commands(entry["command"]):
                action = command.get("action", "unknown")
                action_counts[action] = action_counts.get(action, 0) + int(command.get("amount", 1))
        return action_counts

    def _iter_commands(self, command: dict):
        if "commands" in command:
            yield from command["commands"]
        else:
            yield command
