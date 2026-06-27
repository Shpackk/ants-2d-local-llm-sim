import json
import re
from datetime import datetime
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ALLOWED_ACTIONS = {
    "assign_workers_to_explore",
    "recall_long_explorers",
    "assign_workers_to_food",
    "assign_workers_to_repair",
    "assign_warriors_to_guard",
    "remove_threats",
    "lay_worker_eggs",
    "lay_warrior_eggs",
    "do_nothing",
}


class LLMQueenController:
    def __init__(
        self,
        model_name: str,
        base_url: str = "http://127.0.0.1:1337/v1",
        api_key: str = "jan",
        timeout: float = 8.0,
        debug_log_path: str = "llm_debug.log",
    ) -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.debug_log_path = debug_log_path

    def decide(self, colony_state: dict) -> dict:
        prompt = self._build_prompt(colony_state)
        raw_text = ""

        try:
            raw_text = self._call_model(prompt)
            command_payload = self._extract_json(raw_text)
            validated = self.validate_commands(command_payload, colony_state)
            self._log_decision(colony_state, raw_text, command_payload, validated, None)
            return validated
        except Exception as error:
            fallback = self.fallback_decision(colony_state)
            self._log_decision(colony_state, raw_text, None, fallback, str(error))
            print(f"[LLM Queen] Failed, using fallback. Error: {error}")
            return fallback

    def _call_model(self, prompt: str) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a local offline decision controller. "
                        "You cannot browse. You cannot use tools. "
                        "Return JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.1,
            "max_tokens": 320,
            "stream": False,
        }

        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {error.code}: {body}") from error

        return data["choices"][0]["message"]["content"]

    def _build_prompt(self, colony_state: dict) -> str:
        return f"""
You are running fully offline.

You are not a chatbot.
You are not an internet assistant.
You cannot browse the web.
You cannot search the internet.
You cannot use tools.
You cannot call functions.
You cannot ask questions.
You cannot explain your answer.

You are a local decision controller inside an ant colony simulation.

Goal:
- Reach target_ants living ants before starvation collapse.
- Food locations start hidden. Workers must explore before food can be foraged.
- Food lets queen lay eggs. Eggs hatch after egg_hatch_ticks.
- Every living ant slowly consumes stored food.
- Known food sources regenerate over time, but only up to their capacity.
- If a food source reaches 0, it is depleted forever and cannot regenerate.
- Food source types trade speed for sustainability:
  - small_berries: carry_yield 1, fastest regeneration.
  - rich_fungus: carry_yield 2, medium regeneration.
  - sap_tree: carry_yield 3, slow regeneration.

Allowed actions:
- assign_workers_to_explore
- recall_long_explorers
- assign_workers_to_food
- assign_workers_to_repair
- assign_warriors_to_guard
- remove_threats
- lay_worker_eggs
- lay_warrior_eggs
- do_nothing

Decision rules:
- If known_food_available_sources is 0, explore with idle workers.
- If workers_exploring_too_long is above 0, recall long explorers.
- If known_food_sources is above 0 and food_storage is low, forage with idle workers.
- Returning food carriers are included in workers_available_for_food; assign them to food to make them continue after dropoff.
- If known_food_average_reserve_ratio is low, reduce foraging or explore for more sources.
- If enough workers are idle, split workers between food and exploration instead of using one action.
- If food_storage is safely above food_cost_per_egg and workers are enough to keep foraging, lay worker eggs.
- Account for delayed hatching. Eggs do not help immediately.
- Do not spend all food on eggs; reserve food to prevent starvation.
- Do not drain every known food source to zero if the colony has enough stored food to wait.
- If threats_attacking_nest is above 0, prioritize remove_threats.
- If active_threats is above 0, prioritize remove_threats or warriors guarding.
- If nest_health is below 70, prioritize repairs.
- Repair requires resource_storage or resources_available above 0.
- If nothing useful can be done, use do_nothing.

Amount rules:
- assign_workers_to_explore amount must be between 1 and workers_idle.
- recall_long_explorers amount must be between 1 and workers_exploring_too_long.
- assign_workers_to_food amount is desired total food workers and must be between 1 and workers_available_for_food.
- assign_workers_to_repair amount must be between 1 and workers_idle.
- assign_warriors_to_guard amount must be between 1 and warriors_idle.
- remove_threats amount must be between 1 and warriors_idle.
- lay_worker_eggs amount must be between 1 and 3.
- lay_warrior_eggs amount must be between 1 and 2.
- do_nothing amount must be 0.

Return JSON only.
Do not use markdown.
Do not write text before the JSON.
Do not write text after the JSON.
Return up to 4 commands.
Use multiple commands when splitting workers between food and exploration or when recalling scouts and assigning other workers.
Commands are applied in order.

colony_state:
{json.dumps(colony_state, indent=2)}

Return exactly this schema:
{{
  "commands": [
    {{
      "action": "action_name",
      "amount": 0,
      "target": null
    }}
  ]
}}
""".strip()

    def _extract_json(self, text: str) -> dict:
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON object found in model response: {text}")

        return json.loads(match.group(0))

    def validate_commands(self, command_payload: dict, state: dict) -> dict:
        raw_commands = self._normalize_command_payload(command_payload)
        state_budget = self._build_validation_budget(state)
        validated_commands = []

        for command in raw_commands[:4]:
            validated = self.validate_command(command, state_budget)
            if validated["action"] != "do_nothing":
                validated_commands.append(validated)
                self._consume_validation_budget(validated, state_budget)

        if not validated_commands:
            validated_commands.append({"action": "do_nothing", "amount": 0, "target": None})

        return {"commands": validated_commands}

    def validate_command(self, command: dict, state: dict) -> dict:
        action = command.get("action", "do_nothing")
        amount = command.get("amount", 0)
        target = command.get("target", None)

        try:
            amount = int(amount)
        except (TypeError, ValueError):
            amount = 0

        if action not in ALLOWED_ACTIONS:
            return {"action": "do_nothing", "amount": 0, "target": None}

        workers_idle = int(state.get("workers_idle", 0))
        workers_exploring = int(state.get("workers_exploring", 0))
        workers_exploring_too_long = int(state.get("workers_exploring_too_long", 0))
        workers_available_for_food = int(state.get("workers_available_for_food", workers_idle))
        workers_available_for_food_soon = workers_available_for_food + workers_exploring
        warriors_idle = int(state.get("warriors_idle", 0))
        food_storage = int(state.get("food_storage", 0))
        resource_storage = int(state.get("resource_storage", 0))
        resources_available = int(state.get("resources_available", 0))
        known_food_sources = int(state.get("known_food_sources", 0))
        known_food_available_sources = int(state.get("known_food_available_sources", known_food_sources))
        food_cost_per_egg = int(state.get("food_cost_per_egg", 5))

        if action == "assign_workers_to_explore":
            amount = max(0, min(amount, workers_idle))
        elif action == "recall_long_explorers":
            amount = max(0, min(amount, max(workers_exploring_too_long, workers_exploring)))
        elif action == "assign_workers_to_food":
            if known_food_available_sources <= 0:
                action = "assign_workers_to_explore"
                amount = max(0, min(amount, workers_idle))
            else:
                amount = max(0, min(amount, workers_available_for_food_soon))
        elif action == "assign_workers_to_repair":
            if resource_storage <= 0 and resources_available <= 0:
                action = "do_nothing"
                amount = 0
            else:
                amount = max(0, min(amount, workers_idle))
        elif action == "assign_warriors_to_guard":
            amount = max(0, min(amount, warriors_idle))
        elif action == "remove_threats":
            amount = max(0, min(amount, warriors_idle))
        elif action == "lay_worker_eggs":
            if food_storage < food_cost_per_egg * 2:
                action = "do_nothing"
                amount = 0
            else:
                amount = max(0, min(amount, 3))
        elif action == "lay_warrior_eggs":
            if food_storage < food_cost_per_egg * 3:
                action = "do_nothing"
                amount = 0
            else:
                amount = max(0, min(amount, 2))
        elif action == "do_nothing":
            amount = 0

        if amount <= 0 and action != "do_nothing":
            action = "do_nothing"
            amount = 0

        return {"action": action, "amount": amount, "target": target}

    def _normalize_command_payload(self, command_payload: dict) -> list[dict]:
        if isinstance(command_payload.get("commands"), list):
            return [command for command in command_payload["commands"] if isinstance(command, dict)]

        if "action" in command_payload:
            return [command_payload]

        return [{"action": "do_nothing", "amount": 0, "target": None}]

    def _build_validation_budget(self, state: dict) -> dict:
        return {
            **state,
            "workers_idle": int(state.get("workers_idle", 0)),
            "workers_exploring": int(state.get("workers_exploring", 0)),
            "workers_exploring_too_long": int(state.get("workers_exploring_too_long", 0)),
            "workers_available_for_food": int(state.get("workers_available_for_food", state.get("workers_idle", 0))),
            "workers_foraging": int(state.get("workers_foraging", 0)),
            "warriors_idle": int(state.get("warriors_idle", 0)),
            "food_storage": int(state.get("food_storage", 0)),
        }

    def _consume_validation_budget(self, command: dict, state: dict) -> None:
        action = command["action"]
        amount = command["amount"]
        food_cost_per_egg = int(state.get("food_cost_per_egg", 5))

        if action == "assign_workers_to_explore":
            state["workers_idle"] = max(0, state.get("workers_idle", 0) - amount)
            state["workers_available_for_food"] = max(0, state.get("workers_available_for_food", 0) - amount)
        elif action == "recall_long_explorers":
            state["workers_exploring_too_long"] = max(0, state.get("workers_exploring_too_long", 0) - amount)
            state["workers_exploring"] = max(0, state.get("workers_exploring", 0) - amount)
            state["workers_idle"] = state.get("workers_idle", 0) + amount
            state["workers_available_for_food"] = state.get("workers_available_for_food", 0) + amount
        elif action == "assign_workers_to_food":
            workers_foraging = state.get("workers_foraging", 0)
            new_workers_needed = max(0, amount - workers_foraging)
            state["workers_available_for_food"] = max(0, state.get("workers_available_for_food", 0) - new_workers_needed)
            state["workers_idle"] = max(0, state.get("workers_idle", 0) - new_workers_needed)
            state["workers_foraging"] = max(workers_foraging, amount)
        elif action == "assign_workers_to_repair":
            state["workers_idle"] = max(0, state.get("workers_idle", 0) - amount)
            state["workers_available_for_food"] = max(0, state.get("workers_available_for_food", 0) - amount)
        elif action in ("assign_warriors_to_guard", "remove_threats"):
            state["warriors_idle"] = max(0, state.get("warriors_idle", 0) - amount)
        elif action in ("lay_worker_eggs", "lay_warrior_eggs"):
            state["food_storage"] = max(0, state.get("food_storage", 0) - amount * food_cost_per_egg)

    def _command_batch(self, *commands: dict) -> dict:
        filtered = [command for command in commands if command.get("action") != "do_nothing"]
        if not filtered:
            filtered = [{"action": "do_nothing", "amount": 0, "target": None}]
        return {"commands": filtered[:4]}

    def fallback_decision(self, state: dict) -> dict:
        food_storage = state.get("food_storage", 0)
        resource_storage = state.get("resource_storage", 0)
        resources_available = state.get("resources_available", 0)
        workers_idle = state.get("workers_idle", 0)
        workers_exploring_too_long = state.get("workers_exploring_too_long", 0)
        workers_available_for_food = state.get("workers_available_for_food", workers_idle)
        warriors_idle = state.get("warriors_idle", 0)
        active_threats = state.get("active_threats", 0)
        threats_attacking_nest = state.get("threats_attacking_nest", 0)
        nest_health = state.get("nest_health", 100)
        known_food_sources = state.get("known_food_sources", 0)
        known_food_available_sources = state.get("known_food_available_sources", known_food_sources)
        known_food_remaining = state.get("known_food_remaining", 0)
        known_food_average_reserve_ratio = state.get("known_food_average_reserve_ratio", 0.0)
        food_cost_per_egg = state.get("food_cost_per_egg", 5)

        if (threats_attacking_nest > 0 or active_threats > 0) and warriors_idle > 0:
            return self._command_batch({"action": "remove_threats", "amount": warriors_idle, "target": None})

        if nest_health < 70 and workers_idle > 0 and (resource_storage > 0 or resources_available > 0):
            return self._command_batch({"action": "assign_workers_to_repair", "amount": workers_idle, "target": None})

        if workers_exploring_too_long > 0:
            return self._command_batch({"action": "recall_long_explorers", "amount": workers_exploring_too_long, "target": None})

        if known_food_available_sources <= 0 and workers_idle > 0:
            return self._command_batch({"action": "assign_workers_to_explore", "amount": workers_idle, "target": None})

        if known_food_average_reserve_ratio < 0.2 and food_storage >= 20 and workers_idle > 0:
            return self._command_batch({"action": "assign_workers_to_explore", "amount": workers_idle, "target": None})

        if food_storage < 30 and workers_available_for_food > 0:
            return self._command_batch({"action": "assign_workers_to_food", "amount": workers_available_for_food, "target": None})

        if food_storage >= food_cost_per_egg * 4 and known_food_remaining >= food_cost_per_egg * 2:
            if workers_available_for_food > 0:
                return self._command_batch(
                    {"action": "lay_worker_eggs", "amount": 2, "target": None},
                    {"action": "assign_workers_to_food", "amount": workers_available_for_food, "target": None},
                )
            return self._command_batch({"action": "lay_worker_eggs", "amount": 2, "target": None})

        if workers_available_for_food > 0:
            return self._command_batch({"action": "assign_workers_to_food", "amount": workers_available_for_food, "target": None})

        return self._command_batch({"action": "do_nothing", "amount": 0, "target": None})

    def _log_decision(
        self,
        colony_state: dict,
        raw_text: str,
        parsed_command: dict | None,
        validated_command: dict,
        error: str | None,
    ) -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "model": self.model_name,
            "tick": colony_state.get("tick"),
            "state": colony_state,
            "raw_response": raw_text,
            "parsed_command": parsed_command,
            "validated_command": validated_command,
            "error": error,
        }

        with open(self.debug_log_path, "a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(entry, ensure_ascii=True) + "\n")

        print(f"[LLM Raw] {raw_text.strip()[:240]}")
