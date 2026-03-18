"""
Share of Voice (SoV) Tracker — tracks Trilogy's share of the SAH ad market over time.
Stores weekly snapshots and generates trend data for sparkline charts.
"""
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
SOV_PATH = DATA_DIR / "sov_history.json"


def compute_sov(ads: list[dict]) -> dict:
    """Compute current share of voice metrics."""
    total = len(ads)
    trilogy = sum(1 for a in ads if "trilogy" in a.get("advertiser", "").lower())
    competitors = total - trilogy
    sov_pct = round((trilogy / total) * 100, 1) if total > 0 else 0

    return {
        "trilogy_count": trilogy,
        "competitor_count": competitors,
        "total_count": total,
        "sov_pct": sov_pct,
    }


def append_sov_snapshot(ads: list[dict]) -> list[dict]:
    """Add today's SoV to the historical record."""
    history = load_sov_history()
    today = datetime.now().strftime("%Y-%m-%d")

    # Don't duplicate today's entry
    if history and history[-1].get("date") == today:
        history[-1] = {"date": today, **compute_sov(ads)}
    else:
        history.append({"date": today, **compute_sov(ads)})

    # Keep last 52 weeks
    history = history[-52:]

    SOV_PATH.write_text(json.dumps(history, indent=2))
    return history


def load_sov_history() -> list[dict]:
    """Load SoV history from disk."""
    if SOV_PATH.exists():
        try:
            return json.loads(SOV_PATH.read_text())
        except Exception:
            pass
    return []


def sov_sparkline_svg(history: list[dict], width: int = 200, height: int = 40) -> str:
    """Generate a tiny sparkline SVG of SoV over time."""
    if not history or len(history) < 2:
        return ""

    values = [h.get("sov_pct", 0) for h in history]
    min_v = min(values) - 2
    max_v = max(values) + 2
    range_v = max_v - min_v or 1

    points = []
    for i, v in enumerate(values):
        x = (i / (len(values) - 1)) * width
        y = height - ((v - min_v) / range_v) * height
        points.append(f"{x:.1f},{y:.1f}")

    # Current value for end dot
    last_x = width
    last_y = height - ((values[-1] - min_v) / range_v) * height
    current_val = values[-1]
    prev_val = values[-2] if len(values) >= 2 else current_val
    trend_color = "#31A24C" if current_val >= prev_val else "#E4405F"

    svg = f'<svg width="{width}" height="{height + 10}" viewBox="0 0 {width} {height + 10}" xmlns="http://www.w3.org/2000/svg">'
    # Line
    svg += f'<polyline points="{" ".join(points)}" fill="none" stroke="{trend_color}" stroke-width="2" stroke-linejoin="round"/>'
    # End dot
    svg += f'<circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="3" fill="{trend_color}"/>'
    # Value label
    svg += f'<text x="{width}" y="{height + 9}" text-anchor="end" font-size="10" font-family="-apple-system, sans-serif" fill="{trend_color}" font-weight="700">{current_val}%</text>'
    svg += '</svg>'
    return svg
