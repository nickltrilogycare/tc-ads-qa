"""
Report Generator — produces HTML and terminal reports from analysis results.
"""
import json
from datetime import datetime
from pathlib import Path
from config import REPORTS_DIR


def generate_html_report(
    trilogy_results: list[dict],
    competitor_results: dict[str, list[dict]],
    competitive_analysis: dict,
    report_type: str = "full",
) -> Path:
    """Generate an HTML report with all findings."""

    now = datetime.now()
    filename = f"ads_qa_report_{now:%Y%m%d_%H%M}.html"
    path = REPORTS_DIR / filename

    # Separate poor quality ads
    poor_ads = [r for r in trilogy_results if r.get("overall_score", 100) < 50]
    warning_ads = [r for r in trilogy_results if 50 <= r.get("overall_score", 100) < 70]
    good_ads = [r for r in trilogy_results if r.get("overall_score", 100) >= 70]

    # Build issue summary
    all_issues = []
    for r in trilogy_results:
        for issue in r.get("issues", []):
            issue["ad_source"] = r.get("source_ad", {})
            all_issues.append(issue)

    critical_issues = [i for i in all_issues if i.get("severity") == "critical"]
    high_issues = [i for i in all_issues if i.get("severity") == "high"]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Trilogy Care — Ads QA Report — {now:%d %b %Y}</title>
<style>
  :root {{
    --red: #e74c3c; --orange: #f39c12; --green: #27ae60; --blue: #2980b9;
    --dark: #1a1a2e; --card: #16213e; --text: #eee; --muted: #999;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: var(--dark); color: var(--text); padding: 2rem; line-height: 1.6; }}
  h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
  h2 {{ font-size: 1.3rem; margin: 2rem 0 1rem; border-bottom: 2px solid var(--blue); padding-bottom: 0.3rem; }}
  h3 {{ font-size: 1.1rem; margin: 1rem 0 0.5rem; color: var(--blue); }}
  .meta {{ color: var(--muted); margin-bottom: 2rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1rem 0; }}
  .stat {{ background: var(--card); border-radius: 8px; padding: 1.2rem; text-align: center; }}
  .stat .number {{ font-size: 2rem; font-weight: bold; }}
  .stat .label {{ color: var(--muted); font-size: 0.85rem; }}
  .score-red {{ color: var(--red); }}
  .score-orange {{ color: var(--orange); }}
  .score-green {{ color: var(--green); }}
  .card {{ background: var(--card); border-radius: 8px; padding: 1.2rem; margin: 0.8rem 0; }}
  .card.critical {{ border-left: 4px solid var(--red); }}
  .card.high {{ border-left: 4px solid var(--orange); }}
  .card.medium {{ border-left: 4px solid var(--blue); }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }}
  .badge-critical {{ background: var(--red); }}
  .badge-high {{ background: var(--orange); color: #333; }}
  .badge-medium {{ background: var(--blue); }}
  .badge-low {{ background: #555; }}
  table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
  th, td {{ padding: 0.6rem; text-align: left; border-bottom: 1px solid #333; }}
  th {{ color: var(--muted); font-size: 0.85rem; text-transform: uppercase; }}
  .rec {{ margin: 0.5rem 0; padding: 0.8rem; background: var(--card); border-radius: 6px; }}
  .rec-high {{ border-left: 3px solid var(--red); }}
  .rec-medium {{ border-left: 3px solid var(--orange); }}
  .rec-low {{ border-left: 3px solid var(--blue); }}
</style>
</head>
<body>
<h1>Trilogy Care — Ads QA Report</h1>
<p class="meta">Generated {now:%A %d %B %Y at %H:%M} AEST</p>

<div class="grid">
  <div class="stat">
    <div class="number">{len(trilogy_results)}</div>
    <div class="label">Trilogy Ads Analysed</div>
  </div>
  <div class="stat">
    <div class="number score-red">{len(poor_ads)}</div>
    <div class="label">Poor Quality (&lt;50)</div>
  </div>
  <div class="stat">
    <div class="number score-orange">{len(warning_ads)}</div>
    <div class="label">Needs Work (50-69)</div>
  </div>
  <div class="stat">
    <div class="number score-green">{len(good_ads)}</div>
    <div class="label">Good (70+)</div>
  </div>
  <div class="stat">
    <div class="number">{len(critical_issues)}</div>
    <div class="label">Critical Issues</div>
  </div>
  <div class="stat">
    <div class="number">{sum(len(v) for v in competitor_results.values())}</div>
    <div class="label">Competitor Ads Scraped</div>
  </div>
</div>
"""

    # --- Executive Summary ---
    exec_summary = competitive_analysis.get("executive_summary", "Analysis pending.")
    html += f"""
<h2>Executive Summary</h2>
<div class="card">{exec_summary}</div>
"""

    # --- Critical & High Issues ---
    if critical_issues or high_issues:
        html += "<h2>Priority Issues</h2>"
        for issue in critical_issues + high_issues:
            sev = issue.get("severity", "medium")
            html += f"""
<div class="card {sev}">
  <span class="badge badge-{sev}">{sev.upper()}</span>
  <strong>{issue.get('issue', 'Unknown issue')}</strong>
  <p style="color:var(--muted);margin-top:0.3rem">{issue.get('recommendation', '')}</p>
</div>"""

    # --- Trilogy Ad Scores ---
    html += """
<h2>Trilogy Care Ad Scores</h2>
<table>
<tr><th>Ad #</th><th>Source</th><th>Score</th><th>Copy</th><th>Visual</th><th>Targeting</th><th>Compliance</th><th>Brand</th><th>Fresh</th><th>Type</th></tr>
"""
    for r in sorted(trilogy_results, key=lambda x: x.get("overall_score", 0)):
        score = r.get("overall_score", 0)
        color_class = "score-red" if score < 50 else "score-orange" if score < 70 else "score-green"
        cats = r.get("category_scores", {})
        html += f"""<tr>
  <td>{r.get('source_ad', {}).get('ad_index', '?')}</td>
  <td>{r.get('source_ad', {}).get('source', '?')}</td>
  <td class="{color_class}"><strong>{score}</strong></td>
  <td>{cats.get('copy_quality', {}).get('score', '-')}</td>
  <td>{cats.get('visual_quality', {}).get('score', '-')}</td>
  <td>{cats.get('targeting_signals', {}).get('score', '-')}</td>
  <td>{cats.get('compliance', {}).get('score', '-')}</td>
  <td>{cats.get('brand_consistency', {}).get('score', '-')}</td>
  <td>{cats.get('freshness', {}).get('score', '-')}</td>
  <td>{r.get('ad_type', '?')}</td>
</tr>"""
    html += "</table>"

    # --- Detailed Ad Analysis ---
    html += "<h2>Detailed Ad Analysis</h2>"
    for r in trilogy_results:
        score = r.get("overall_score", 0)
        color_class = "score-red" if score < 50 else "score-orange" if score < 70 else "score-green"
        html += f"""
<div class="card">
  <h3>Ad #{r.get('source_ad', {}).get('ad_index', '?')} — <span class="{color_class}">{score}/100</span></h3>
  <p><strong>Copy:</strong> {r.get('copy_text_extracted', 'N/A')[:200]}</p>
  <p><strong>CTA:</strong> {r.get('cta_identified', 'None identified')}</p>
  <p><strong>Strengths:</strong> {', '.join(r.get('strengths', []))}</p>
"""
        for issue in r.get("issues", []):
            sev = issue.get("severity", "low")
            html += f'  <p><span class="badge badge-{sev}">{sev}</span> {issue.get("issue", "")}</p>\n'
        html += "</div>"

    # --- Competitive Analysis ---
    html += "<h2>Competitive Intelligence</h2>"

    # Strengths & Weaknesses
    strengths = competitive_analysis.get("trilogy_strengths", [])
    weaknesses = competitive_analysis.get("trilogy_weaknesses", [])
    if strengths:
        html += "<h3>Trilogy Strengths vs Market</h3><ul>"
        for s in strengths:
            html += f"<li>{s}</li>"
        html += "</ul>"
    if weaknesses:
        html += "<h3>Gaps vs Competitors</h3><ul>"
        for w in weaknesses:
            html += f"<li style='color:var(--orange)'>{w}</li>"
        html += "</ul>"

    # Competitor details
    comp_highlights = competitive_analysis.get("competitor_highlights", {})
    for name, info in comp_highlights.items():
        if isinstance(info, dict):
            html += f"""
<div class="card">
  <h3>{name}</h3>
  <p><strong>Notable:</strong> {info.get('notable_ads', 'N/A')}</p>
  <p><strong>Threats:</strong> <span style="color:var(--red)">{info.get('threats', 'N/A')}</span></p>
  <p><strong>Opportunities:</strong> <span style="color:var(--green)">{info.get('opportunities', 'N/A')}</span></p>
</div>"""

    # Recommendations
    recs = competitive_analysis.get("recommendations", [])
    if recs:
        html += "<h2>Recommendations</h2>"
        for rec in recs:
            pri = rec.get("priority", "medium")
            html += f"""
<div class="rec rec-{pri}">
  <span class="badge badge-{pri}">{pri.upper()}</span>
  <strong>{rec.get('action', '')}</strong>
  <p style="color:var(--muted)">{rec.get('rationale', '')}</p>
</div>"""

    # Market trends
    trends = competitive_analysis.get("market_trends", [])
    if trends:
        html += "<h2>Market Trends</h2><ul>"
        for t in trends:
            html += f"<li>{t}</li>"
        html += "</ul>"

    html += """
<hr style="margin-top:3rem;border-color:#333">
<p class="meta">Report generated by TC Ads QA Tool. Screenshots saved in /screenshots/</p>
</body>
</html>"""

    path.write_text(html)
    print(f"\n  Report saved: {path}")
    return path


def print_terminal_summary(
    trilogy_results: list[dict],
    competitive_analysis: dict,
):
    """Print a concise summary to terminal."""
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel

    console = Console()

    # Header
    console.print("\n[bold blue]━━━ Trilogy Care Ads QA Report ━━━[/bold blue]\n")

    # Executive summary
    exec_summary = competitive_analysis.get("executive_summary", "Pending.")
    console.print(Panel(exec_summary, title="Executive Summary", border_style="blue"))

    # Score table
    table = Table(title="Trilogy Ad Scores")
    table.add_column("Ad #", style="dim")
    table.add_column("Source")
    table.add_column("Score", justify="center")
    table.add_column("Type")
    table.add_column("Key Issue")

    for r in sorted(trilogy_results, key=lambda x: x.get("overall_score", 0)):
        score = r.get("overall_score", 0)
        score_style = "red" if score < 50 else "yellow" if score < 70 else "green"
        issues = r.get("issues", [])
        top_issue = issues[0].get("issue", "—") if issues else "—"

        table.add_row(
            str(r.get("source_ad", {}).get("ad_index", "?")),
            r.get("source_ad", {}).get("source", "?"),
            f"[{score_style}]{score}[/{score_style}]",
            r.get("ad_type", "?"),
            top_issue[:60],
        )

    console.print(table)

    # Recommendations
    recs = competitive_analysis.get("recommendations", [])
    if recs:
        console.print("\n[bold]Top Recommendations:[/bold]")
        for rec in recs[:5]:
            pri = rec.get("priority", "medium")
            color = "red" if pri == "high" else "yellow" if pri == "medium" else "blue"
            console.print(f"  [{color}]■[/{color}] {rec.get('action', '')}")

    console.print()
