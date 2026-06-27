# Ants 2D

Small Pygame ant colony simulation with a local LLM queen controller.

## What It Does

- Runs a 2D ant colony with workers, warriors, food, resources, threats, nest health, and eggs. (P.S. warriors/nest dmg/restoration is noop)
- Uses Jan Local API Server for offline queen decisions.
- Sends colony state to LLM every few seconds, validates JSON response, then executes colony commands.
- Supports commands like gathering food, gathering repair resources, repairing nest, guarding, removing threats, and laying eggs.

## LLM Setup

Start Local API Server and load the working model before running the sim. (I used Jan to run models)

API endpoint used:

```text
http://127.0.0.1:1337/v1/chat/completions
```

Qwen3.5-9B model works well for this project. Qwen3.5-4B was a failure in testing.

Keep Jan tools, MCP, and web-search features disabled for this project.
Qwen3.5-4B was constantly trying to hit web-search, so I switched to 9B.

## Run

```powershell
python test_jan_api.py
python main.py
```

## First runs
- Qwen3.5-4B - too dumb (or maybe I am too dumb to make it work here, or maybe maybe)
- Qwen3_5-9B-Q5_K_M - starves food sources till 0, does not explore new sources if 1 is available, thus waists time when the first source is drained to find a new one. After all sources of food are drained it tends to send everyone to explore, even though it has enough food to reach the goal while all current ants are idle, eventually colony dies.
- gemma-4-12B-it-Q5_K_M - same thing as Qwen3_5-9B-Q5_K_M (but eats way more compute power from GPU)
- Mistral-NeMo-12B-Abliterated_i1-Q5_K_M - "pressing all buttons". Sent ants to explore, next call call them back, then assign to gather food even though no food was found. Felt like a cat that stepped on the keyboard.
- Qwythos-9B-Claude-Mythos-5-1M-Q6_K - reached the "possible end game state" as other models, but way faster, still didn't take the path of "produce more ants to get to the goal" and kept sending ants to explore and called them back again. Result = dead colony. (eats wopping 26gb - 16vram + 10ram. Highest currently. Other models ran only on vram and consumed 8-10gb)

### Another iteration on prompt
- Qwythos-9B-Claude-Mythos-5-1M-Q6_K - went on "aggressive expansion" sacrificng food for currently alive workers. Produce 4 - 2 dies, produce 2 - 1 dies, food ran out - colony died.

Other models were not tested since was in the process of prompt adjustment.

### Iteration: "Hint"
Added goal math, food reserve math, and “safe egg” count. Prompt now hints: compare goal progress before exploring, idle is okay, don’t explore unless more food is truly needed, use food gathering and egg laying together, and never spend food to zero. Also blocked bad fallback behavior where “no food source” became forced exploration.

- Qwythos-9B-Claude-Mythos-5-1M-Q6_K - won.
- Qwen3_5-9B-Q5_K_M - won.
- gemma-4-12B-it-Q5_K_M - won.

## Observations
Models don't like "idle", they need explicit commands or hinst, "idle" + "you can achieve the goal with current state" = will lead to nothing. "you can achieve the goal" + "hint on how to achieve the goal" = model can do it.

## Notes
Written with GPT-5.5 medium reasoning.
