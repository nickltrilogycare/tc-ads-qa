"""
Ad Creator Dashboard — generates an HTML review page for created ad campaigns.
Shows all generated ads with hooks, copy variants, visual briefs, and QA results.
Marketing team can review, approve, and export.
"""
import json
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "ad_output"


def generate_creator_dashboard() -> Path:
    """Generate an HTML dashboard from the latest ad batch."""
    # Find latest batch
    batches = sorted(OUTPUT_DIR.glob("ad_batch_*[!_summary].json"), reverse=True)
    if not batches:
        print("No ad batches found")
        return None

    data = json.loads(batches[0].read_text())
    now = datetime.now()
    path = OUTPUT_DIR / "ad_review_dashboard.html"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TC Ad Creator — Review Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #F0F2F5; --white: #FFFFFF; --card: #FFFFFF;
  --border: #DADDE1; --text: #1C1E21; --muted: #65676B; --light: #8A8D91;
  --accent: #007F7E; --accent2: #43C0BE; --blue: #2c4c79;
  --green: #31A24C; --yellow: #F7B928; --red: #E4405F; --orange: #F58220;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'Inter', -apple-system, sans-serif; background: var(--bg); color: var(--text); }}

.header {{
  background: var(--blue); color: white; padding: 20px 32px;
}}
.header h1 {{ font-size: 22px; font-weight: 700; }}
.header p {{ font-size: 13px; opacity: 0.8; margin-top: 4px; }}

.stats {{
  display: flex; gap: 16px; padding: 20px 32px; flex-wrap: wrap;
}}
.stat {{
  background: var(--white); border-radius: 10px; padding: 16px 24px;
  flex: 1; min-width: 140px; text-align: center;
  border: 1px solid var(--border);
}}
.stat .n {{ font-size: 28px; font-weight: 700; }}
.stat .l {{ font-size: 11px; color: var(--muted); margin-top: 2px; }}

.campaign {{
  background: var(--white); margin: 16px 32px; border-radius: 12px;
  border: 1px solid var(--border); overflow: hidden;
}}
.campaign-header {{
  padding: 20px 24px; border-bottom: 1px solid var(--border);
  display: flex; align-items: center; gap: 16px;
}}
.campaign-header h2 {{ font-size: 18px; font-weight: 700; flex: 1; }}
.badge {{ padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
.badge-approved {{ background: #E8F5E9; color: var(--green); }}
.badge-revision {{ background: #FFF3E0; color: var(--orange); }}
.badge-rejected {{ background: #FFEBE9; color: var(--red); }}

.campaign-body {{ padding: 24px; }}
.section {{ margin-bottom: 24px; }}
.section h3 {{
  font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;
  color: var(--muted); margin-bottom: 8px; font-weight: 600;
}}

.hook-card {{
  background: var(--bg); border-radius: 8px; padding: 12px 16px;
  margin-bottom: 8px; border-left: 3px solid var(--accent);
}}
.hook-card .type {{ font-size: 11px; color: var(--accent); font-weight: 600; text-transform: uppercase; }}
.hook-card .text {{ font-size: 15px; font-weight: 600; margin-top: 4px; line-height: 1.5; }}
.hook-card .score {{ font-size: 12px; color: var(--muted); margin-top: 4px; }}

.copy-variant {{
  background: var(--bg); border-radius: 8px; padding: 16px; margin-bottom: 12px;
}}
.copy-variant .label {{ font-size: 11px; color: var(--accent); font-weight: 600; margin-bottom: 8px; }}
.copy-variant .headline {{ font-size: 16px; font-weight: 700; color: var(--blue); margin-bottom: 8px; }}
.copy-variant .primary {{ font-size: 14px; line-height: 1.6; margin-bottom: 8px; }}
.copy-variant .cta {{ display: inline-block; background: var(--accent); color: white; padding: 6px 16px; border-radius: 6px; font-size: 13px; font-weight: 600; }}

.visual-brief {{
  background: linear-gradient(135deg, #f0f7f7, #eef5ff); border-radius: 8px;
  padding: 16px; margin-bottom: 12px;
}}
.visual-brief .prompt {{ font-size: 14px; line-height: 1.6; font-style: italic; color: var(--blue); }}
.visual-brief .details {{ font-size: 13px; color: var(--muted); margin-top: 8px; }}

.qa-result {{ display: flex; gap: 16px; flex-wrap: wrap; }}
.qa-score {{
  width: 80px; height: 80px; border-radius: 50%; display: flex;
  align-items: center; justify-content: center; font-size: 24px;
  font-weight: 700; color: white; flex-shrink: 0;
}}
.qa-flags {{ flex: 1; }}
.qa-flag {{
  display: flex; gap: 8px; padding: 6px 0; font-size: 13px;
  border-bottom: 1px solid var(--border);
}}
.qa-flag:last-child {{ border: none; }}
.flag-dot {{ width: 8px; height: 8px; border-radius: 50%; margin-top: 5px; flex-shrink: 0; }}

.meta-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }}
.meta-item {{ background: var(--bg); padding: 10px 14px; border-radius: 6px; }}
.meta-item .label {{ font-size: 11px; color: var(--muted); font-weight: 600; text-transform: uppercase; }}
.meta-item .value {{ font-size: 14px; font-weight: 500; margin-top: 2px; }}
</style>
</head>
<body>
<div class="header" style="display:flex;align-items:center;gap:16px;">
  <div style="flex:1;">
    <h1>TC Ad Creator — Review Dashboard</h1>
    <p>{now:%d %B %Y} · {len(data)} campaigns generated · Review and approve before production</p>
  </div>
  <a href="index.html" style="padding:8px 16px;background:rgba(255,255,255,0.2);color:white;border-radius:6px;font-size:14px;font-weight:600;text-decoration:none;display:inline-flex;align-items:center;gap:6px;">
    ← Back to Intelligence
  </a>
</div>
"""

    # Stats
    approved = sum(1 for r in data if r.get("qa_review", {}).get("overall_verdict") == "APPROVED")
    revision = sum(1 for r in data if r.get("qa_review", {}).get("overall_verdict") == "NEEDS_REVISION")
    scores = [r.get("qa_review", {}).get("overall_score", 0) for r in data]
    avg_score = round(sum(scores) / len(scores)) if scores else 0

    html += f"""
<div class="stats">
  <div class="stat"><div class="n">{len(data)}</div><div class="l">Campaigns</div></div>
  <div class="stat"><div class="n" style="color:var(--green)">{approved}</div><div class="l">Approved</div></div>
  <div class="stat"><div class="n" style="color:var(--orange)">{revision}</div><div class="l">Need Revision</div></div>
  <div class="stat"><div class="n">{avg_score}</div><div class="l">Avg QA Score</div></div>
</div>
"""

    # Campaigns
    for r in data:
        strategy = r.get("strategy", {})
        hooks = r.get("hooks", [])
        copy = r.get("ad_copy", [])
        visual = r.get("visual_brief", {})
        qa = r.get("qa_review", {})

        verdict = qa.get("overall_verdict", "UNKNOWN")
        score = qa.get("overall_score", 0)
        score_bg = "var(--green)" if score >= 75 else "var(--orange)" if score >= 60 else "var(--red)"
        badge_class = "badge-approved" if verdict == "APPROVED" else "badge-revision" if verdict == "NEEDS_REVISION" else "badge-rejected"

        html += f"""
<div class="campaign">
  <div class="campaign-header">
    <h2>{strategy.get('campaign_name', 'Untitled')}</h2>
    <span class="badge {badge_class}">{verdict}</span>
  </div>
  <div class="campaign-body">

    <div class="section">
      <h3>Campaign Details</h3>
      <div class="meta-grid">
        <div class="meta-item"><div class="label">Platform</div><div class="value">{strategy.get('platform', '?')}</div></div>
        <div class="meta-item"><div class="label">Format</div><div class="value">{strategy.get('format', '?')}</div></div>
        <div class="meta-item"><div class="label">Objective</div><div class="value">{strategy.get('objective', '?')}</div></div>
        <div class="meta-item"><div class="label">Messaging Angle</div><div class="value">{strategy.get('messaging_angle', '?')}</div></div>
        <div class="meta-item"><div class="label">Target</div><div class="value">{strategy.get('target_audience', '?')}</div></div>
        <div class="meta-item"><div class="label">Framework</div><div class="value">{strategy.get('copy_framework', '?')}</div></div>
      </div>
    </div>

    <div class="section">
      <h3>Hooks (Top 3)</h3>
"""
        for h in (hooks[:3] if hooks else []):
            if isinstance(h, dict) and "error" not in h:
                html += f"""      <div class="hook-card">
        <div class="type">{h.get('hook_type', '?')}</div>
        <div class="text">{h.get('hook_text', 'N/A')}</div>
        <div class="score">Strength: {h.get('estimated_strength', '?')}/10</div>
      </div>\n"""

        html += '    </div>\n\n    <div class="section">\n      <h3>Ad Copy Variants</h3>\n'
        for c in (copy if isinstance(copy, list) else [copy]):
            if isinstance(c, dict) and "error" not in c:
                html += f"""      <div class="copy-variant">
        <div class="label">Variant {c.get('ab_variant', '?')} · {c.get('copy_framework_used', '?')}</div>
        <div class="headline">{c.get('headline', 'N/A')}</div>
        <div class="primary">{c.get('primary_text', 'N/A')}</div>
        <span class="cta">{c.get('cta_button', 'Learn More')}</span>
      </div>\n"""

        html += '    </div>\n\n    <div class="section">\n      <h3>Visual Brief (Higgsfield)</h3>\n'
        if isinstance(visual, dict) and "error" not in visual:
            html += f"""      <div class="visual-brief">
        <div class="prompt">{visual.get('higgsfield_prompt', visual.get('scene_description', 'N/A'))}</div>
        <div class="details">
          Setting: {visual.get('setting', 'N/A')} ·
          People: {visual.get('people', 'N/A')} ·
          Mood: {', '.join(visual.get('mood_board_keywords', [])[:5])}
        </div>
      </div>\n"""

        html += '    </div>\n\n    <div class="section">\n      <h3>QA Review</h3>\n'
        html += f"""      <div class="qa-result">
        <div class="qa-score" style="background:{score_bg}">{score}</div>
        <div class="qa-flags">
"""
        for flag in qa.get("revision_suggestions", qa.get("flags", []))[:5]:
            if isinstance(flag, dict):
                sev = flag.get("priority", flag.get("severity", "medium"))
                dc = "var(--red)" if sev in ("high", "critical") else "var(--orange)" if sev == "medium" else "var(--light)"
                html += f'          <div class="qa-flag"><span class="flag-dot" style="background:{dc}"></span>{flag.get("suggestion", flag.get("issue", ""))}</div>\n'

        html += """        </div>
      </div>
    </div>
  </div>
</div>
"""

    html += f"""
<div style="text-align:center;padding:32px;color:var(--muted);font-size:13px;">
  Generated by TC Ad Creator · {now:%d %B %Y %H:%M} · {len(data)} campaigns
</div>
</body>
</html>"""

    path.write_text(html)
    print(f"  Ad review dashboard: {path}")
    return path


if __name__ == "__main__":
    p = generate_creator_dashboard()
    if p:
        import subprocess
        subprocess.run(["open", str(p)])
