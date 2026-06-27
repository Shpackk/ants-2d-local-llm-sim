## Overall read

- `gemma-4-12B-it-abliterated-uncensored_i1-Q5_K_M`: fastest growth. Best if goal is shortest win time.
- `Qwen3_5-9B-Q5_K_M`: second fastest, best final food reserve and clean explorer handling.
- `empero-ai\Qwythos-9B-Claude-Mythos-5-1M-Q6_K`: slowest, most conservative, cleanest final worker state.

## Key results

| Model | Result | Win tick | 50 ants | 90 ants | Final food | Final explorers | Deaths |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `gemma-4-12B-it-abliterated-uncensored_i1-Q5_K_M` | win | 15524 | 9500 | 14500 | 239 | 86 | 0 |
| `Qwen3_5-9B-Q5_K_M` | win | 16627 | 11000 | 16000 | 264 | 60 | 0 |
| `empero-ai\Qwythos-9B-Claude-Mythos-5-1M-Q6_K` | win | 20295 | 14000 | 19000 | 212 | 0 | 0 |

## Observations

### Gemma

Fastest model. Reached target at tick `15524`, about `1103` ticks before Qwen and `4771` before Qwythos. It laid workers aggressively: `57` eggs by tick `10000`, highest by far. This early reproduction explains most of the win.

Weakness: poor final worker cleanup. Ended with `86` workers exploring and `3` exploring too long. So it wins fast, but leaves many workers in stale assignments.

### Qwen

Balanced model. Won at tick `16627`, close to Gemma but with better reserves: `264` final food and `6600` buffer ticks, best of all runs. Ended with `60` explorers and `0` too long, cleaner than Gemma.

It was slower early than Gemma: `41` eggs by tick `10000` vs Gemma `57`. Still much faster than Qwythos.

### Qwythos

Most conservative. Won at tick `20295`, slowest run. Early egg laying lagged badly: only `24` eggs by tick `10000`, and `38` by tick `12000`. It had peak food `429`, suggesting it gathered/held food instead of converting it into ants fast enough.

Strength: clean final state. Ended with `99` idle workers and `0` explorers. It also recalled `97` explorers total, much more than other models. But this cleanup came with slow growth.

## Bottom line

For this scenario, best performance mostly means laying worker eggs early enough. Gemma did that best. Qwen was slightly slower but more resource-efficient. Qwythos looked cautious and orderly, but too slow.

These runs do not test combat, scarce food, random seeds, hidden-map variance, or long-term survival after food depletion.
