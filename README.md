# Ants 2D

Small Pygame ant colony simulation with a local LLM queen controller.

## What It Does

- Runs a 2D ant colony with workers, warriors, food, resources, threats, nest health, and eggs.
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

## Notes

Written with GPT-5.5 medium reasoning.
