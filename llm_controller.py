import json
import re
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ALLOWED_ACTIONS = {
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
    ) -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def decide(self, colony_state: dict) -> dict:
        prompt = self._build_prompt(colony_state)

        try:
            raw_text = self._call_model(prompt)
            command = self._extract_json(raw_text)
            return self.validate_command(command, colony_state)
        except Exception as error:
            print(f"[LLM Queen] Failed, using fallback. Error: {error}")
            return self.fallback_decision(colony_state)

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
            "max_tokens": 128,
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

Your only job is to read the colony_state JSON and return exactly one JSON command.

Allowed actions:
- assign_workers_to_food
- assign_workers_to_repair
- assign_warriors_to_guard
- remove_threats
- lay_worker_eggs
- lay_warrior_eggs
- do_nothing

Decision rules:
- If threats_attacking_nest is above 0, prioritize remove_threats.
- If active_threats is above 0, prioritize remove_threats or warriors guarding.
- If nest_health is below 70, prioritize repairs.
- Repair requires resource_storage or resources_available above 0.
- If food_storage is below 50, prioritize assigning workers to food.
- If food_storage is above 100 and there are idle workers, laying eggs is allowed.
- If nothing useful can be done, use do_nothing.

Amount rules:
- assign_workers_to_food amount must be between 1 and workers_idle.
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

colony_state:
{json.dumps(colony_state, indent=2)}

Return exactly this schema:
{{
  "action": "action_name",
  "amount": 0,
  "target": null
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
        warriors_idle = int(state.get("warriors_idle", 0))
        food_storage = int(state.get("food_storage", 0))
        resource_storage = int(state.get("resource_storage", 0))
        resources_available = int(state.get("resources_available", 0))

        if action == "assign_workers_to_food":
            amount = max(0, min(amount, workers_idle))
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
            if food_storage < 100:
                action = "do_nothing"
                amount = 0
            else:
                amount = max(0, min(amount, 3))
        elif action == "lay_warrior_eggs":
            if food_storage < 120:
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

    def fallback_decision(self, state: dict) -> dict:
        food_storage = state.get("food_storage", 0)
        resource_storage = state.get("resource_storage", 0)
        resources_available = state.get("resources_available", 0)
        workers_idle = state.get("workers_idle", 0)
        warriors_idle = state.get("warriors_idle", 0)
        active_threats = state.get("active_threats", 0)
        threats_attacking_nest = state.get("threats_attacking_nest", 0)
        nest_health = state.get("nest_health", 100)

        if (threats_attacking_nest > 0 or active_threats > 0) and warriors_idle > 0:
            return {"action": "remove_threats", "amount": warriors_idle, "target": None}

        if nest_health < 70 and workers_idle > 0 and (resource_storage > 0 or resources_available > 0):
            return {
                "action": "assign_workers_to_repair",
                "amount": workers_idle,
                "target": None,
            }

        if food_storage < 50 and workers_idle > 0:
            return {
                "action": "assign_workers_to_food",
                "amount": workers_idle,
                "target": None,
            }

        if food_storage > 100:
            return {"action": "lay_worker_eggs", "amount": 2, "target": None}

        return {"action": "do_nothing", "amount": 0, "target": None}
