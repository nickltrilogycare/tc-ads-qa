"""
Action Queue — generates a prioritized list of marketing actions
based on all available intelligence (scores, gaps, competitor moves, landing pages).
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def generate_action_queue() -> list[dict]:
    """Generate a prioritized action list from all available data."""
    actions = []

    # 1. From messaging gaps
    try:
        gaps = json.loads((DATA_DIR / "messaging_gaps.json").read_text())
        for g in gaps.get("gaps", {}).get("gaps", [])[:3]:
            angle = g["angle"].replace("_", " ").title()
            actions.append({
                "priority": "high",
                "category": "Creative",
                "action": f"Create ads using '{angle}' messaging",
                "detail": f"{g['competitor_count']} competitors use this angle. Trilogy has 0 ads.",
                "owner": "Creative Team",
            })
    except Exception:
        pass

    # 2. From landing page analysis
    try:
        lps = json.loads((DATA_DIR / "landing_pages.json").read_text())
        trilogy_lps = [lp for lp in lps if "trilogy" in lp.get("label", "").lower()]
        for lp in trilogy_lps:
            if not lp.get("has_form"):
                actions.append({
                    "priority": "high",
                    "category": "Conversion",
                    "action": "Add lead capture form to Trilogy landing pages",
                    "detail": "Bolton Clarke and Dovida both have forms. Trilogy's ad landing pages have no form — potential conversion leak.",
                    "owner": "Digital Team",
                })
                break
    except Exception:
        pass

    # 3. From video analysis
    try:
        videos = json.loads((DATA_DIR / "video_analyses.json").read_text())
        trilogy_videos = [v for v in videos if "trilogy" in v.get("advertiser", "").lower()]
        for v in trilogy_videos:
            for imp in v.get("improvements", [])[:2]:
                actions.append({
                    "priority": "medium",
                    "category": "Video",
                    "action": imp,
                    "detail": f"From AI analysis of Trilogy video ad (score: {v.get('video_score', '?')}/100)",
                    "owner": "Creative Team",
                })
    except Exception:
        pass

    # 4. From messaging analysis — low share angles
    try:
        msg = json.loads((DATA_DIR / "messaging_analysis.json").read_text())
        for angle, share in msg.get("trilogy_share", {}).items():
            if share < 30:
                label = angle.replace("_", " ").title()
                total = msg["messaging_distribution"].get(angle, 0)
                actions.append({
                    "priority": "medium",
                    "category": "Strategy",
                    "action": f"Increase '{label}' messaging (currently {share}% share)",
                    "detail": f"{total} market ads use this angle. Trilogy under-represented.",
                    "owner": "Marketing Strategy",
                })
    except Exception:
        pass

    # 5. General weekly actions
    actions.append({
        "priority": "low",
        "category": "Monitoring",
        "action": "Run weekly ad scrape to track competitor changes",
        "detail": "python3 main.py from tc-ads-qa directory",
        "owner": "Marketing Coordinator",
    })

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    actions.sort(key=lambda x: priority_order.get(x["priority"], 3))

    return actions


def get_action_queue_html() -> str:
    """Generate HTML for the action queue panel."""
    actions = generate_action_queue()

    rows = ""
    for a in actions:
        color = "#E4405F" if a["priority"] == "high" else "#F7B928" if a["priority"] == "medium" else "#1877F2"
        rows += f"""
    <div style="display:flex;gap:12px;padding:12px 0;border-bottom:1px solid #E4E6EB;align-items:start;">
      <span style="background:{color};color:white;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;text-transform:uppercase;white-space:nowrap;margin-top:2px;">{a['priority']}</span>
      <div style="flex:1;">
        <div style="font-size:14px;font-weight:600;color:#1C1E21;">{a['action']}</div>
        <div style="font-size:12px;color:#65676B;margin-top:2px;">{a['detail']}</div>
      </div>
      <span style="font-size:11px;color:#8A8D91;white-space:nowrap;background:#F0F2F5;padding:2px 8px;border-radius:4px;">{a['owner']}</span>
    </div>"""

    return f"""
<div class="score-logic" id="actionQueue" style="margin-top:24px;">
  <h3>Action Queue — What to Do Next</h3>
  <p style="font-size:14px;color:var(--text-secondary);margin-bottom:16px;">
    Prioritized actions based on competitive intelligence, gap analysis, and landing page audit.
    {len(actions)} actions identified.
  </p>
  {rows}
</div>
"""
