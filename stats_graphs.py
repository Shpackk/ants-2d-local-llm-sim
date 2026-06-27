import argparse
import html
import json
import re
from pathlib import Path


PANEL_HEIGHT = 230
PANEL_TITLE_HEIGHT = 34
LEGEND_HEIGHT = 34
PLOT_HEIGHT = PANEL_HEIGHT - PANEL_TITLE_HEIGHT - LEGEND_HEIGHT
WIDTH = 1200
MARGIN_LEFT = 72
MARGIN_RIGHT = 28
MARGIN_TOP = 112
MARGIN_BOTTOM = 52
PANEL_GAP = 96
CHART_WIDTH = WIDTH - MARGIN_LEFT - MARGIN_RIGHT
LEGEND_ITEM_WIDTH = 230
COLORS = ["#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c", "#0891b2"]


PANELS = [
    {
        "title": "Colony progress",
        "series": [
            ("living_ants", "Living ants"),
            ("target_ants", "Target ants"),
            ("eggs", "Eggs"),
        ],
    },
    {
        "title": "Food economy",
        "series": [
            ("food_storage", "Stored food"),
            ("food_in_transit", "Food in transit"),
            ("known_food_remaining", "Known food left"),
            ("map_food_remaining", "Map food left"),
        ],
    },
    {
        "title": "Worker behavior",
        "series": [
            ("workers_idle", "Idle"),
            ("workers_foraging", "Foraging"),
            ("workers_returning_with_food", "Returning food"),
            ("workers_exploring", "Exploring"),
        ],
    },
    {
        "title": "LLM decisions and discovery",
        "series": [
            ("queen_command_count", "Queen commands"),
            ("llm_found_food_sources", "Food sources found"),
            ("known_food_available_sources", "Known food available"),
        ],
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create SVG trend graphs from every stats/*.json simulation report."
    )
    parser.add_argument("--stats-dir", default="stats", help="Folder containing stats JSON files.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Folder for generated graphs. Defaults to <stats-dir>/graphs.",
    )
    args = parser.parse_args()

    stats_dir = Path(args.stats_dir)
    output_dir = Path(args.output_dir) if args.output_dir else stats_dir / "graphs"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_files = sorted(path for path in stats_dir.glob("*.json") if path.is_file())
    if not json_files:
        print(f"No JSON files found in {stats_dir}")
        return 0

    written = []
    for json_path in json_files:
        try:
            report = json.loads(json_path.read_text(encoding="utf-8"))
            svg = build_svg(report, json_path.name)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"Skipped {json_path}: {exc}")
            continue

        output_path = output_dir / output_name(report, json_path)
        output_path.write_text(svg, encoding="utf-8")
        written.append(output_path)
        print(f"Wrote {output_path}")

    print(f"Created {len(written)} graph(s) in {output_dir}")
    return 0


def build_svg(report: dict, source_name: str) -> str:
    samples = report.get("samples") or []
    if not samples and isinstance(report.get("summary"), dict):
        samples = [report["summary"]]
    if not samples:
        raise ValueError("report has no samples")

    model_name = str(report.get("model_name") or report.get("metadata", {}).get("model_name") or "unknown-model")
    outcome = report.get("outcome") or {}
    result = outcome.get("result", "unknown")
    final_tick = outcome.get("tick", samples[-1].get("tick", "unknown"))

    height = MARGIN_TOP + MARGIN_BOTTOM + len(PANELS) * PANEL_HEIGHT + (len(PANELS) - 1) * PANEL_GAP
    tick_values = [number(sample.get("tick")) for sample in samples]
    tick_min = min(tick_values)
    tick_max = max(tick_values)
    if tick_min == tick_max:
        tick_max = tick_min + 1

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}">',
        "<style>",
        "text{font-family:Arial,Helvetica,sans-serif;fill:#111827}",
        ".muted{fill:#6b7280;font-size:13px}",
        ".title{font-size:24px;font-weight:700}",
        ".panel-title{font-size:16px;font-weight:700}",
        ".axis{stroke:#d1d5db;stroke-width:1}",
        ".grid{stroke:#e5e7eb;stroke-width:1}",
        ".line{fill:none;stroke-width:2.5;stroke-linejoin:round;stroke-linecap:round}",
        ".legend{font-size:12px;fill:#374151}",
        "</style>",
        f'<rect x="0" y="0" width="{WIDTH}" height="{height}" fill="#ffffff"/>',
        f'<text class="title" x="{MARGIN_LEFT}" y="30">{escape(model_name)}</text>',
        (
            f'<text class="muted" x="{MARGIN_LEFT}" y="50">'
            f"Source: {escape(source_name)} | Result: {escape(str(result))} | Final tick: {escape(str(final_tick))}"
            "</text>"
        ),
    ]

    for index, panel in enumerate(PANELS):
        y_top = MARGIN_TOP + index * (PANEL_HEIGHT + PANEL_GAP)
        parts.extend(draw_panel(panel, samples, tick_min, tick_max, y_top))

    parts.append("</svg>")
    return "\n".join(parts)


def draw_panel(panel: dict, samples: list[dict], tick_min: float, tick_max: float, y_top: int) -> list[str]:
    plot_top = y_top + PANEL_TITLE_HEIGHT + LEGEND_HEIGHT
    y_bottom = plot_top + PLOT_HEIGHT
    values_by_key = {
        key: [number(sample.get(key)) for sample in samples]
        for key, _label in panel["series"]
        if any(is_number(sample.get(key)) for sample in samples)
    }
    all_values = [value for values in values_by_key.values() for value in values]
    y_min = min(0, min(all_values, default=0))
    y_max = max(all_values, default=1)
    if y_min == y_max:
        y_max = y_min + 1

    parts = [
        f'<text class="panel-title" x="{MARGIN_LEFT}" y="{y_top}">{escape(panel["title"])}</text>',
        f'<line class="axis" x1="{MARGIN_LEFT}" y1="{y_bottom}" x2="{WIDTH - MARGIN_RIGHT}" y2="{y_bottom}"/>',
        f'<line class="axis" x1="{MARGIN_LEFT}" y1="{plot_top}" x2="{MARGIN_LEFT}" y2="{y_bottom}"/>',
    ]

    for ratio in (0, 0.25, 0.5, 0.75, 1):
        y = y_bottom - ratio * PLOT_HEIGHT
        value = y_min + ratio * (y_max - y_min)
        parts.append(f'<line class="grid" x1="{MARGIN_LEFT}" y1="{fmt(y)}" x2="{WIDTH - MARGIN_RIGHT}" y2="{fmt(y)}"/>')
        parts.append(f'<text class="muted" x="10" y="{fmt(y + 4)}">{format_value(value)}</text>')

    for ratio in (0, 0.25, 0.5, 0.75, 1):
        x = MARGIN_LEFT + ratio * CHART_WIDTH
        tick = tick_min + ratio * (tick_max - tick_min)
        parts.append(f'<text class="muted" text-anchor="middle" x="{fmt(x)}" y="{y_bottom + 22}">{format_value(tick)}</text>')
    parts.append(f'<text class="muted" text-anchor="end" x="{WIDTH - MARGIN_RIGHT}" y="{y_bottom + 38}">tick</text>')

    legend_x = MARGIN_LEFT
    legend_y = y_top + PANEL_TITLE_HEIGHT
    color_index = 0
    for key, label in panel["series"]:
        values = values_by_key.get(key)
        if not values:
            continue
        color = COLORS[color_index % len(COLORS)]
        color_index += 1
        points = [
            f"{fmt(scale_x(number(sample.get('tick')), tick_min, tick_max))},{fmt(scale_y(number(sample.get(key)), y_min, y_max, plot_top, y_bottom))}"
            for sample in samples
        ]
        parts.append(f'<polyline class="line" stroke="{color}" points="{" ".join(points)}"/>')
        parts.append(f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x + 22}" y2="{legend_y}" stroke="{color}" stroke-width="3"/>')
        parts.append(f'<text class="legend" x="{legend_x + 28}" y="{legend_y + 4}">{escape(label)}</text>')
        legend_x += LEGEND_ITEM_WIDTH

    return parts


def output_name(report: dict, json_path: Path) -> str:
    model_name = str(report.get("model_name") or report.get("metadata", {}).get("model_name") or "unknown-model")
    safe_model = safe_filename(model_name)
    return f"{safe_model}__{json_path.stem}.svg"


def safe_filename(value: str) -> str:
    value = value.replace("\\", "_").replace("/", "_")
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    return value[:120] or "unknown-model"


def scale_x(tick: float, tick_min: float, tick_max: float) -> float:
    return MARGIN_LEFT + ((tick - tick_min) / (tick_max - tick_min)) * CHART_WIDTH


def scale_y(value: float, y_min: float, y_max: float, y_top: int, y_bottom: int) -> float:
    return y_bottom - ((value - y_min) / (y_max - y_min)) * (y_bottom - y_top)


def is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def number(value) -> float:
    return float(value) if is_number(value) else 0.0


def format_value(value: float) -> str:
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    if value == int(value):
        return str(int(value))
    return f"{value:.1f}"


def fmt(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def escape(value: str) -> str:
    return html.escape(value, quote=True)


if __name__ == "__main__":
    raise SystemExit(main())
