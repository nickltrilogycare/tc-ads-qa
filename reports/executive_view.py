"""
Executive View — 30-second dashboard summary for the CMO.
5 key numbers + 3 action items. That's it.
"""
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def get_executive_view_html(
    cards: list[dict],
    competitive_analysis: dict,
    messaging_gaps: dict = None,
) -> str:
    """Generate the executive summary section for the dashboard."""
    now = datetime.now()

    # Key numbers
    trilogy = [c for c in cards if c.get("advertiser") == "Trilogy Care"]
    competitors = [c for c in cards if c.get("advertiser") != "Trilogy Care"]
    trilogy_scores = [c["score"] for c in trilogy if c.get("score", -1) >= 0]
    comp_scores = [c["score"] for c in competitors if c.get("score", -1) >= 0]

    avg_trilogy = round(sum(trilogy_scores) / len(trilogy_scores), 1) if trilogy_scores else 0
    avg_comp = round(sum(comp_scores) / len(comp_scores), 1) if comp_scores else 0
    score_gap = round(avg_trilogy - avg_comp, 1)

    poor_trilogy = sum(1 for s in trilogy_scores if s < 50)
    num_advertisers = len(set(c.get("advertiser", "") for c in competitors))

    # Video vs static split
    video_count = sum(1 for c in trilogy if c.get("format") == "video")
    total_trilogy = len(trilogy)

    # Top action items
    actions = []
    recs = competitive_analysis.get("recommendations", [])
    for r in recs[:2]:
        actions.append(r.get("action", ""))

    # Gap-based action
    if messaging_gaps:
        gaps = messaging_gaps.get("gaps", {}).get("gaps", [])
        if gaps:
            angle = gaps[0]["angle"].replace("_", " ").title()
            actions.append(f"Fill messaging gap: {angle} ({gaps[0]['competitor_count']} competitor ads, 0 Trilogy)")

    if poor_trilogy > 0 and len(actions) < 3:
        actions.append(f"Review {poor_trilogy} low-scoring ads for optimization or removal")

    while len(actions) < 3:
        actions.append("Continue weekly monitoring")

    # Build HTML
    score_delta_color = "var(--green)" if score_gap > 0 else "var(--red)" if score_gap < -5 else "var(--yellow)"
    score_arrow = "↑" if score_gap > 0 else "↓" if score_gap < 0 else "→"

    html = f"""
<div class="exec-view" id="execView">
  <div class="exec-header">
    <h2>Executive Brief — {now:%d %b %Y}</h2>
    <p style="font-size:13px;color:var(--text-tertiary);margin-top:2px;">30-second overview for the leadership team</p>
  </div>

  <div class="exec-numbers">
    <div class="exec-num">
      <div class="exec-val" style="color:var(--accent)">{len(trilogy)}</div>
      <div class="exec-label">Our Active Ads</div>
    </div>
    <div class="exec-num">
      <div class="exec-val">{num_advertisers}</div>
      <div class="exec-label">Competitors Tracked</div>
    </div>
    <div class="exec-num">
      <div class="exec-val" style="color:{'var(--green)' if avg_trilogy >= 70 else 'var(--yellow)' if avg_trilogy >= 50 else 'var(--red)'}">{avg_trilogy}</div>
      <div class="exec-label">Our Avg Score</div>
    </div>
    <div class="exec-num">
      <div class="exec-val" style="color:{score_delta_color}">{score_arrow} {abs(score_gap)}</div>
      <div class="exec-label">vs Competitor Avg</div>
    </div>
    <div class="exec-num">
      <div class="exec-val">{video_count}/{total_trilogy}</div>
      <div class="exec-label">Video / Total</div>
    </div>
  </div>

  <div class="exec-actions">
    <h3 style="font-size:14px;color:var(--text-secondary);margin-bottom:8px;">This Week's Actions</h3>
    {"".join(f'<div class="exec-action"><span class="exec-action-num">{i+1}</span>{a}</div>' for i, a in enumerate(actions[:3]))}
  </div>
</div>
"""
    return html


def get_executive_view_css() -> str:
    return """
.exec-view {
  background: var(--white); border: 2px solid var(--accent);
  border-radius: var(--radius-lg); padding: 24px; margin-top: 24px;
  display: none;
}
.exec-view.visible { display: block; }
.exec-header { margin-bottom: 16px; }
.exec-header h2 { font-size: 18px; color: var(--accent); }
.exec-numbers {
  display: flex; gap: 12px; margin-bottom: 20px;
}
.exec-num {
  flex: 1; text-align: center; padding: 12px;
  background: var(--bg); border-radius: var(--radius);
}
.exec-val { font-size: 28px; font-weight: 700; }
.exec-label { font-size: 11px; color: var(--text-tertiary); margin-top: 2px; }
.exec-actions { }
.exec-action {
  display: flex; align-items: start; gap: 10px; padding: 10px 0;
  border-bottom: 1px solid var(--border-light); font-size: 14px;
}
.exec-action:last-child { border: none; }
.exec-action-num {
  width: 24px; height: 24px; border-radius: 50%;
  background: var(--accent); color: white; display: flex;
  align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; flex-shrink: 0;
}
@media (max-width: 768px) {
  .exec-numbers { flex-direction: column; }
}
"""
