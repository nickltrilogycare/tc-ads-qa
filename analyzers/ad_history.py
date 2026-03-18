"""
Ad history tracking for freshness indicators.

Maintains a cumulative JSON file (data/ad_history.json) that tracks when ads
were first/last seen, enabling freshness classification: new, running,
long_running, stopped.
"""

import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
HISTORY_PATH = BASE_DIR / "data" / "ad_history.json"

TODAY = date.today().isoformat()


def _load_history() -> dict[str, dict]:
    """Load existing history from disk, or return empty dict."""
    if HISTORY_PATH.exists():
        with open(HISTORY_PATH, "r") as f:
            return json.load(f)
    return {}


def _save_history(history: dict[str, dict]) -> None:
    """Persist history to disk."""
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2, sort_keys=True)


def _ad_key(ad: dict) -> str:
    """Derive a unique key for an ad.

    Prefers library_id; falls back to a composite of advertiser + ad_index.
    """
    lid = ad.get("library_id")
    if lid:
        return str(lid)
    # Fallback for ads without a library_id
    return f"{ad.get('advertiser', 'unknown')}_{ad.get('ad_index', 'unknown')}"


def update_history(current_ads: list[dict], today: str | None = None) -> dict[str, dict]:
    """Update the cumulative history file with the current scan results.

    Args:
        current_ads: List of ad dicts from the latest scan.
        today: Override for today's date string (ISO format). Defaults to
               actual today.

    Returns:
        The updated history dict.
    """
    today = today or date.today().isoformat()
    history = _load_history()

    # Build set of keys seen in the current scan
    seen_keys: set[str] = set()

    for ad in current_ads:
        key = _ad_key(ad)
        seen_keys.add(key)

        if key in history:
            # Existing ad -- update last_seen and ensure active
            history[key]["last_seen"] = today
            history[key]["status"] = "active"
        else:
            # New ad
            history[key] = {
                "first_seen": today,
                "last_seen": today,
                "status": "active",
                "advertiser": ad.get("advertiser", "unknown"),
                "source": ad.get("source", "unknown"),
            }

    # Mark ads not in current scan as stopped
    for key, entry in history.items():
        if key not in seen_keys and entry["status"] == "active":
            entry["status"] = "stopped"

    _save_history(history)
    return history


def classify_ad(entry: dict, today: str | None = None) -> dict[str, Any]:
    """Return freshness classification for a single history entry.

    Returns a dict with keys: freshness, days_running.
    """
    today_dt = date.fromisoformat(today or date.today().isoformat())
    first_seen_dt = date.fromisoformat(entry["first_seen"])
    last_seen_dt = date.fromisoformat(entry["last_seen"])
    days_running = (last_seen_dt - first_seen_dt).days

    if entry["status"] == "stopped":
        freshness = "stopped"
    elif entry["first_seen"] == (today or date.today().isoformat()):
        freshness = "new"
    elif days_running > 30:
        freshness = "long_running"
    else:
        freshness = "running"

    return {
        "freshness": freshness,
        "days_running": days_running,
        "first_seen": entry["first_seen"],
        "last_seen": entry["last_seen"],
        "status": entry["status"],
    }


def get_freshness_stats(today: str | None = None) -> dict[str, int]:
    """Return aggregate freshness counts across all tracked ads.

    Returns dict with keys: total, new, running, long_running, stopped.
    """
    history = _load_history()
    stats = {"total": 0, "new": 0, "running": 0, "long_running": 0, "stopped": 0}

    for entry in history.values():
        info = classify_ad(entry, today=today)
        stats["total"] += 1
        stats[info["freshness"]] += 1

    return stats


def enrich_ads(ads: list[dict], today: str | None = None) -> list[dict]:
    """Add freshness data to each ad dict in-place and return the list.

    Adds keys: freshness, days_running, first_seen, last_seen.
    Ads not found in history are tagged freshness='unknown'.
    """
    history = _load_history()

    for ad in ads:
        key = _ad_key(ad)
        entry = history.get(key)
        if entry:
            info = classify_ad(entry, today=today)
            ad["freshness"] = info["freshness"]
            ad["days_running"] = info["days_running"]
            ad["first_seen_history"] = info["first_seen"]
            ad["last_seen_history"] = info["last_seen"]
        else:
            ad["freshness"] = "unknown"
            ad["days_running"] = 0
            ad["first_seen_history"] = None
            ad["last_seen_history"] = None

    return ads
