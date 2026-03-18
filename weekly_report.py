#!/usr/bin/env python3
"""
Weekly Ads QA Report — runs the full pipeline and tracks changes week-over-week.
Designed to be run via launchd/cron every Monday morning.
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import DATA_DIR, REPORTS_DIR
from main import run_full_pipeline


def load_previous_results() -> dict | None:
    """Load the most recent full results file for comparison."""
    results_files = sorted(DATA_DIR.glob("full_results_*.json"), reverse=True)
    # Skip the first one (current run) — get the previous
    for f in results_files:
        try:
            data = json.loads(f.read_text())
            run_date = datetime.fromisoformat(data.get("run_date", ""))
            # Only compare with results older than 1 day
            if run_date < datetime.now() - timedelta(days=1):
                return data
        except Exception:
            continue
    return None


def compute_week_over_week(current: dict, previous: dict) -> dict:
    """Compare current vs previous week's results."""
    changes = {
        "period": {
            "current": current.get("run_date"),
            "previous": previous.get("run_date"),
        },
        "trilogy": {
            "ads_current": len(current.get("trilogy_results", [])),
            "ads_previous": len(previous.get("trilogy_results", [])),
        },
        "score_changes": [],
        "new_issues": [],
        "resolved_issues": [],
    }

    # Average score comparison
    curr_scores = [r.get("overall_score", 0) for r in current.get("trilogy_results", []) if "overall_score" in r]
    prev_scores = [r.get("overall_score", 0) for r in previous.get("trilogy_results", []) if "overall_score" in r]

    if curr_scores and prev_scores:
        changes["avg_score_current"] = round(sum(curr_scores) / len(curr_scores), 1)
        changes["avg_score_previous"] = round(sum(prev_scores) / len(prev_scores), 1)
        changes["score_delta"] = round(changes["avg_score_current"] - changes["avg_score_previous"], 1)

    # Issue comparison
    curr_issues = set()
    prev_issues = set()
    for r in current.get("trilogy_results", []):
        for issue in r.get("issues", []):
            curr_issues.add(issue.get("issue", ""))
    for r in previous.get("trilogy_results", []):
        for issue in r.get("issues", []):
            prev_issues.add(issue.get("issue", ""))

    changes["new_issues"] = list(curr_issues - prev_issues)
    changes["resolved_issues"] = list(prev_issues - curr_issues)

    return changes


def run_weekly():
    """Execute weekly report with WoW comparison."""
    print("\n" + "=" * 60)
    print("  WEEKLY ADS QA REPORT")
    print(f"  Week of {datetime.now():%d %B %Y}")
    print("=" * 60)

    # Run the full pipeline
    report_path = run_full_pipeline(
        include_competitors=True,
        platforms=["facebook", "google"],
    )

    # Load current and previous results
    results_files = sorted(DATA_DIR.glob("full_results_*.json"), reverse=True)
    if results_files:
        current = json.loads(results_files[0].read_text())
    else:
        print("  [!] No results file found")
        return

    previous = load_previous_results()
    if previous:
        print("\n  Comparing with previous run...")
        wow = compute_week_over_week(current, previous)

        # Save WoW comparison
        wow_path = DATA_DIR / f"wow_comparison_{datetime.now():%Y%m%d}.json"
        with open(wow_path, "w") as f:
            json.dump(wow, f, indent=2, default=str)

        print(f"\n  Week-over-Week Changes:")
        print(f"    Ads: {wow['trilogy']['ads_previous']} → {wow['trilogy']['ads_current']}")
        if "score_delta" in wow:
            delta = wow["score_delta"]
            arrow = "↑" if delta > 0 else "↓" if delta < 0 else "→"
            print(f"    Avg Score: {wow['avg_score_previous']} → {wow['avg_score_current']} ({arrow} {abs(delta)})")
        if wow["new_issues"]:
            print(f"    New Issues: {len(wow['new_issues'])}")
            for i in wow["new_issues"][:3]:
                print(f"      - {i}")
        if wow["resolved_issues"]:
            print(f"    Resolved: {len(wow['resolved_issues'])}")
    else:
        print("\n  No previous results for comparison (first run)")

    print(f"\n  Report: {report_path}")


if __name__ == "__main__":
    run_weekly()
