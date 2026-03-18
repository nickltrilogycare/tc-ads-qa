"""
Visual Ads Dashboard Generator
Modelled on Foreplay.co / MagicBrief — masonry grid with filterable ad cards,
clickable images, and quality scores.
"""
import base64
import json
from datetime import datetime
from pathlib import Path
from config import REPORTS_DIR

AD_IMAGES_DIR = Path(__file__).parent.parent / "ad_images"


def image_to_base64(path: str) -> str:
    """Convert a local image to base64 data URI."""
    p = Path(path)
    if not p.exists():
        return ""
    suffix = p.suffix.lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "gif": "image/gif", "webp": "image/webp"}.get(suffix.lstrip("."), "image/png")
    try:
        data = p.read_bytes()
        b64 = base64.b64encode(data).decode()
        return f"data:{mime};base64,{b64}"
    except Exception:
        return ""


def get_image_src(ad: dict) -> str:
    """Get the best image source for an ad card."""
    # Try element screenshot first
    el_ss = ad.get("element_screenshot")
    if el_ss:
        b64 = image_to_base64(el_ss)
        if b64:
            return b64

    # Try downloaded images
    for path in ad.get("image_paths", []):
        if path.startswith("/") or path.startswith("C:"):
            b64 = image_to_base64(path)
            if b64:
                return b64
        elif path.startswith("http"):
            return path

    # Try image URLs
    for url in ad.get("image_urls", []):
        if url.startswith("http"):
            return url

    return ""


def score_color(score: int) -> str:
    if score >= 70:
        return "#27ae60"
    elif score >= 50:
        return "#f39c12"
    else:
        return "#e74c3c"


def score_label(score: int) -> str:
    if score >= 80:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Needs Work"
    elif score >= 30:
        return "Poor"
    else:
        return "Critical"


def format_icon(ad_format: str) -> str:
    icons = {
        "video": '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>',
        "image": '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>',
        "text": '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>',
        "carousel": '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>',
    }
    return icons.get(ad_format, icons["image"])


def platform_icon(source: str) -> str:
    if source == "facebook":
        return '<svg width="18" height="18" viewBox="0 0 24 24" fill="#1877F2"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>'
    else:
        return '<svg width="18" height="18" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>'


def generate_dashboard(
    all_ads: list[dict],
    analysis_results: list[dict],
    competitive_analysis: dict,
) -> Path:
    """Generate a Foreplay-style visual dashboard HTML file."""
    now = datetime.now()
    filename = f"ads_dashboard_{now:%Y%m%d_%H%M}.html"
    path = REPORTS_DIR / filename

    # Build a lookup from analysis results to ads
    score_map = {}
    for r in analysis_results:
        src = r.get("source_ad", {})
        key = f"{src.get('source', '')}_{src.get('advertiser', '')}_{src.get('ad_index', '')}"
        score_map[key] = r

    # Get unique advertisers and platforms
    advertisers = sorted(set(a.get("advertiser", "Unknown") for a in all_ads))
    platforms = sorted(set(a.get("source", "unknown") for a in all_ads))
    formats = sorted(set(a.get("ad_format", "unknown") for a in all_ads))

    # Build card data
    cards_json = []
    for ad in all_ads:
        key = f"{ad.get('source', '')}_{ad.get('advertiser', '')}_{ad.get('ad_index', '')}"
        analysis = score_map.get(key, {})
        score = analysis.get("overall_score", -1)
        img_src = get_image_src(ad)

        card = {
            "advertiser": ad.get("advertiser", "Unknown"),
            "source": ad.get("source", "unknown"),
            "ad_format": ad.get("ad_format", "unknown"),
            "ad_index": ad.get("ad_index", 0),
            "ad_url": ad.get("ad_url", "#"),
            "library_id": ad.get("library_id", ""),
            "start_date": ad.get("start_date", ""),
            "copy_text": (ad.get("copy_text") or ad.get("full_text", ""))[:300],
            "cta": ad.get("cta") or analysis.get("cta_identified", ""),
            "score": score,
            "score_color": score_color(score) if score >= 0 else "#555",
            "score_label": score_label(score) if score >= 0 else "Pending",
            "has_multiple_versions": ad.get("has_multiple_versions", False),
            "version_count": ad.get("version_count", 1),
            "img_src": img_src,
            "issues": analysis.get("issues", []),
            "strengths": analysis.get("strengths", []),
            "category_scores": analysis.get("category_scores", {}),
        }
        cards_json.append(card)

    # Summary stats
    trilogy_cards = [c for c in cards_json if "trilogy" in c["advertiser"].lower() or "Trilogy" in c["advertiser"]]
    comp_cards = [c for c in cards_json if c not in trilogy_cards]
    trilogy_scores = [c["score"] for c in trilogy_cards if c["score"] >= 0]
    avg_score = round(sum(trilogy_scores) / len(trilogy_scores), 1) if trilogy_scores else 0
    poor_count = sum(1 for s in trilogy_scores if s < 50)
    good_count = sum(1 for s in trilogy_scores if s >= 70)

    exec_summary = competitive_analysis.get("executive_summary", "")
    recommendations = competitive_analysis.get("recommendations", [])
    trilogy_strengths = competitive_analysis.get("trilogy_strengths", [])
    trilogy_weaknesses = competitive_analysis.get("trilogy_weaknesses", [])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TC Ads QA Dashboard — {now:%d %b %Y}</title>
<style>
:root {{
  --bg: #0f1117;
  --surface: #1a1d27;
  --surface2: #232736;
  --border: #2d3148;
  --text: #e4e6f0;
  --muted: #8b8fa3;
  --accent: #6366f1;
  --accent2: #818cf8;
  --green: #22c55e;
  --yellow: #eab308;
  --red: #ef4444;
  --blue: #3b82f6;
  --fb: #1877F2;
  --google: #4285F4;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
       background: var(--bg); color: var(--text); overflow-x: hidden; }}

/* ── Top Nav ── */
.topbar {{
  position: sticky; top: 0; z-index: 100;
  background: rgba(15,17,23,0.92); backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  padding: 12px 24px; display: flex; align-items: center; gap: 16px;
}}
.topbar h1 {{ font-size: 1.1rem; font-weight: 700; white-space: nowrap; }}
.topbar .logo {{ color: var(--accent); }}
.topbar .date {{ color: var(--muted); font-size: 0.8rem; margin-left: auto; }}

/* ── Stats Bar ── */
.stats-bar {{
  display: flex; gap: 12px; padding: 16px 24px; flex-wrap: wrap;
  border-bottom: 1px solid var(--border);
}}
.stat-pill {{
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 12px 20px; display: flex; flex-direction: column; align-items: center;
  min-width: 110px;
}}
.stat-pill .num {{ font-size: 1.6rem; font-weight: 700; }}
.stat-pill .lbl {{ font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px; }}

/* ── Layout ── */
.layout {{ display: flex; min-height: calc(100vh - 140px); }}

/* ── Sidebar ── */
.sidebar {{
  width: 260px; min-width: 260px; padding: 20px 16px;
  border-right: 1px solid var(--border); overflow-y: auto;
  background: var(--surface);
}}
.sidebar h3 {{
  font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px;
  color: var(--muted); margin: 16px 0 8px; font-weight: 600;
}}
.sidebar h3:first-child {{ margin-top: 0; }}
.filter-group {{ margin-bottom: 4px; }}
.filter-btn {{
  display: flex; align-items: center; gap: 8px;
  width: 100%; padding: 7px 10px; border: none; border-radius: 6px;
  background: transparent; color: var(--text); cursor: pointer;
  font-size: 0.85rem; text-align: left; transition: background 0.15s;
}}
.filter-btn:hover {{ background: var(--surface2); }}
.filter-btn.active {{ background: var(--accent); color: white; }}
.filter-btn .count {{
  margin-left: auto; background: var(--surface2); color: var(--muted);
  padding: 1px 7px; border-radius: 10px; font-size: 0.75rem;
}}
.filter-btn.active .count {{ background: rgba(255,255,255,0.2); color: white; }}

/* Score range filter */
.score-filter {{ display: flex; gap: 6px; flex-wrap: wrap; margin: 4px 0; }}
.score-chip {{
  padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600;
  cursor: pointer; border: 1px solid var(--border); background: transparent;
  color: var(--text); transition: all 0.15s;
}}
.score-chip:hover {{ border-color: var(--accent); }}
.score-chip.active {{ border-color: transparent; color: white; }}
.score-chip[data-range="good"].active {{ background: var(--green); }}
.score-chip[data-range="ok"].active {{ background: var(--yellow); color: #333; }}
.score-chip[data-range="poor"].active {{ background: var(--red); }}
.score-chip[data-range="all"].active {{ background: var(--accent); }}

/* View toggle */
.view-toggle {{ display: flex; gap: 4px; margin: 8px 0; }}
.view-btn {{
  flex: 1; padding: 6px; border: 1px solid var(--border); border-radius: 6px;
  background: transparent; color: var(--muted); cursor: pointer; font-size: 0.75rem;
  text-align: center; transition: all 0.15s;
}}
.view-btn.active {{ background: var(--accent); border-color: var(--accent); color: white; }}

/* Detail toggle */
.detail-toggle {{ margin: 8px 0; }}
.toggle-row {{
  display: flex; align-items: center; justify-content: space-between;
  padding: 5px 0; font-size: 0.82rem;
}}
.toggle-switch {{
  width: 36px; height: 20px; border-radius: 10px; background: var(--border);
  position: relative; cursor: pointer; transition: background 0.2s;
}}
.toggle-switch.on {{ background: var(--accent); }}
.toggle-switch::after {{
  content: ''; position: absolute; top: 2px; left: 2px;
  width: 16px; height: 16px; border-radius: 50%; background: white;
  transition: transform 0.2s;
}}
.toggle-switch.on::after {{ transform: translateX(16px); }}

/* ── Main Content ── */
.main {{ flex: 1; padding: 20px; overflow-y: auto; }}

/* Masonry Grid */
.masonry {{
  column-count: 4; column-gap: 16px;
}}
@media (max-width: 1400px) {{ .masonry {{ column-count: 3; }} }}
@media (max-width: 1000px) {{ .masonry {{ column-count: 2; }} }}
@media (max-width: 600px) {{ .masonry {{ column-count: 1; }} }}

/* ── Ad Card ── */
.ad-card {{
  break-inside: avoid; background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; margin-bottom: 16px; overflow: hidden;
  transition: transform 0.15s, box-shadow 0.15s; cursor: pointer;
}}
.ad-card:hover {{
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.3);
  border-color: var(--accent);
}}
.ad-card.hidden {{ display: none; }}

/* Card Header */
.card-header {{
  display: flex; align-items: center; gap: 8px;
  padding: 10px 12px; border-bottom: 1px solid var(--border);
}}
.card-header .platform-icon {{ display: flex; align-items: center; }}
.card-header .advertiser {{
  font-size: 0.82rem; font-weight: 600; flex: 1;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.card-header .score-badge {{
  padding: 2px 8px; border-radius: 6px; font-size: 0.72rem;
  font-weight: 700; color: white; white-space: nowrap;
}}

/* Card Image */
.card-image {{
  position: relative; background: var(--surface2);
  min-height: 120px; display: flex; align-items: center; justify-content: center;
}}
.card-image img {{
  width: 100%; height: auto; display: block;
}}
.card-image .no-image {{
  color: var(--muted); font-size: 0.8rem; padding: 40px;
  text-align: center;
}}
.card-image .format-badge {{
  position: absolute; top: 8px; left: 8px;
  background: rgba(0,0,0,0.7); backdrop-filter: blur(4px);
  padding: 3px 8px; border-radius: 4px; font-size: 0.7rem;
  display: flex; align-items: center; gap: 4px; color: white;
}}
.card-image .video-overlay {{
  position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
  width: 48px; height: 48px; background: rgba(0,0,0,0.6);
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
}}
.card-image .video-overlay svg {{ fill: white; }}
.card-image .versions-badge {{
  position: absolute; top: 8px; right: 8px;
  background: var(--accent); color: white;
  padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 600;
}}

/* Card Body */
.card-body {{ padding: 10px 12px; }}
.card-body .copy {{
  font-size: 0.82rem; line-height: 1.5; color: var(--text);
  display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical;
  overflow: hidden; margin-bottom: 8px;
}}
.card-body .meta-row {{
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-top: 6px;
}}
.card-body .tag {{
  padding: 2px 8px; border-radius: 4px; font-size: 0.7rem;
  background: var(--surface2); color: var(--muted); border: 1px solid var(--border);
}}
.card-body .tag.cta {{ background: rgba(99,102,241,0.15); color: var(--accent2); border-color: rgba(99,102,241,0.3); }}
.card-body .tag.date {{ background: rgba(59,130,246,0.1); color: var(--blue); border-color: rgba(59,130,246,0.2); }}

/* Card Footer - Issues */
.card-footer {{
  padding: 8px 12px; border-top: 1px solid var(--border);
  font-size: 0.75rem;
}}
.card-footer .issue {{
  display: flex; align-items: start; gap: 6px; margin: 3px 0;
}}
.card-footer .issue-dot {{
  width: 6px; height: 6px; border-radius: 50%; margin-top: 5px; flex-shrink: 0;
}}
.card-footer .issue-dot.critical {{ background: var(--red); }}
.card-footer .issue-dot.high {{ background: var(--yellow); }}
.card-footer .issue-dot.medium {{ background: var(--blue); }}
.card-footer .issue-dot.low {{ background: var(--muted); }}

/* Score breakdown popup */
.score-detail {{
  display: none; padding: 10px 12px; border-top: 1px solid var(--border);
  background: var(--surface2);
}}
.ad-card:hover .score-detail {{ display: block; }}
.score-bar-row {{
  display: flex; align-items: center; gap: 8px; margin: 3px 0;
  font-size: 0.72rem;
}}
.score-bar-label {{ width: 70px; color: var(--muted); text-align: right; }}
.score-bar {{
  flex: 1; height: 4px; background: var(--border); border-radius: 2px;
  overflow: hidden;
}}
.score-bar-fill {{ height: 100%; border-radius: 2px; transition: width 0.3s; }}
.score-bar-val {{ width: 28px; font-weight: 600; font-size: 0.7rem; }}

/* ── Insights Panel ── */
.insights-panel {{
  padding: 20px 24px; border-bottom: 1px solid var(--border);
  background: var(--surface); display: none;
}}
.insights-panel.visible {{ display: block; }}
.insights-panel h2 {{
  font-size: 1rem; margin-bottom: 12px; color: var(--accent2);
}}
.insights-grid {{
  display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}}
.insight-card {{
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: 10px; padding: 14px;
}}
.insight-card h4 {{
  font-size: 0.8rem; color: var(--muted); text-transform: uppercase;
  letter-spacing: 0.5px; margin-bottom: 8px;
}}
.insight-card ul {{ list-style: none; padding: 0; }}
.insight-card li {{
  padding: 4px 0; font-size: 0.85rem; line-height: 1.4;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}}
.insight-card li:last-child {{ border: none; }}
.rec-priority {{
  display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px;
}}
.rec-priority.high {{ background: var(--red); }}
.rec-priority.medium {{ background: var(--yellow); }}
.rec-priority.low {{ background: var(--blue); }}

/* Search */
.search-box {{
  width: 100%; padding: 8px 12px; border: 1px solid var(--border);
  border-radius: 8px; background: var(--surface2); color: var(--text);
  font-size: 0.85rem; margin-bottom: 12px; outline: none;
}}
.search-box:focus {{ border-color: var(--accent); }}
.search-box::placeholder {{ color: var(--muted); }}

/* Empty state */
.empty-state {{
  text-align: center; padding: 60px 20px; color: var(--muted);
}}
.empty-state svg {{ margin-bottom: 12px; }}
</style>
</head>
<body>

<!-- Top Bar -->
<div class="topbar">
  <span class="logo">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
  </span>
  <h1>Trilogy Care — Ads QA Dashboard</h1>
  <button onclick="toggleInsights()" style="background:var(--accent);color:white;border:none;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:0.8rem;font-weight:600;">
    Insights
  </button>
  <span class="date">{now:%A %d %B %Y}</span>
</div>

<!-- Stats Bar -->
<div class="stats-bar">
  <div class="stat-pill">
    <div class="num">{len(all_ads)}</div>
    <div class="lbl">Total Ads</div>
  </div>
  <div class="stat-pill">
    <div class="num">{len(trilogy_cards)}</div>
    <div class="lbl">Trilogy Ads</div>
  </div>
  <div class="stat-pill">
    <div class="num">{len(comp_cards)}</div>
    <div class="lbl">Competitor Ads</div>
  </div>
  <div class="stat-pill">
    <div class="num" style="color:{score_color(int(avg_score))}">{avg_score}</div>
    <div class="lbl">Avg Trilogy Score</div>
  </div>
  <div class="stat-pill">
    <div class="num" style="color:var(--green)">{good_count}</div>
    <div class="lbl">Good (70+)</div>
  </div>
  <div class="stat-pill">
    <div class="num" style="color:var(--red)">{poor_count}</div>
    <div class="lbl">Poor (&lt;50)</div>
  </div>
</div>

<!-- Insights Panel (hidden by default) -->
<div class="insights-panel" id="insightsPanel">
  <h2>Competitive Intelligence</h2>
  <p style="color:var(--text);margin-bottom:16px;font-size:0.9rem;">{exec_summary}</p>
  <div class="insights-grid">
    <div class="insight-card">
      <h4>Trilogy Strengths</h4>
      <ul>
        {"".join(f'<li style="color:var(--green)">+ {s}</li>' for s in trilogy_strengths)}
      </ul>
    </div>
    <div class="insight-card">
      <h4>Gaps vs Competitors</h4>
      <ul>
        {"".join(f'<li style="color:var(--yellow)">- {w}</li>' for w in trilogy_weaknesses)}
      </ul>
    </div>
    <div class="insight-card">
      <h4>Recommendations</h4>
      <ul>
        {"".join(f'<li><span class="rec-priority {r.get("priority","medium")}"></span>{r.get("action","")}</li>' for r in recommendations)}
      </ul>
    </div>
  </div>
</div>

<!-- Layout -->
<div class="layout">
  <!-- Sidebar -->
  <div class="sidebar">
    <input type="text" class="search-box" placeholder="Search ads..." oninput="filterCards()">

    <h3>View</h3>
    <div class="view-toggle">
      <button class="view-btn active" onclick="setView('masonry',this)">Grid</button>
      <button class="view-btn" onclick="setView('list',this)">List</button>
    </div>

    <h3>Show on Cards</h3>
    <div class="detail-toggle">
      <div class="toggle-row">Copy <div class="toggle-switch on" onclick="toggleDetail('copy',this)"></div></div>
      <div class="toggle-row">Issues <div class="toggle-switch on" onclick="toggleDetail('issues',this)"></div></div>
      <div class="toggle-row">Score Bars <div class="toggle-switch" onclick="toggleDetail('scores',this)"></div></div>
    </div>

    <h3>Quality Score</h3>
    <div class="score-filter">
      <div class="score-chip active" data-range="all" onclick="setScoreFilter('all',this)">All</div>
      <div class="score-chip" data-range="good" onclick="setScoreFilter('good',this)">Good 70+</div>
      <div class="score-chip" data-range="ok" onclick="setScoreFilter('ok',this)">OK 50-69</div>
      <div class="score-chip" data-range="poor" onclick="setScoreFilter('poor',this)">Poor &lt;50</div>
    </div>

    <h3>Advertiser</h3>
"""

    # Advertiser filter buttons
    advertiser_counts = {}
    for c in cards_json:
        adv = c["advertiser"]
        advertiser_counts[adv] = advertiser_counts.get(adv, 0) + 1

    html += '    <div class="filter-group">\n'
    html += f'      <button class="filter-btn active" data-filter="advertiser" data-value="all" onclick="setFilter(\'advertiser\',\'all\',this)">All Advertisers <span class="count">{len(all_ads)}</span></button>\n'
    for adv in sorted(advertiser_counts.keys()):
        is_trilogy = "trilogy" in adv.lower()
        display = "Trilogy Care" if is_trilogy else adv.replace("_", " ")
        html += f'      <button class="filter-btn" data-filter="advertiser" data-value="{adv}" onclick="setFilter(\'advertiser\',\'{adv}\',this)">{"" if not is_trilogy else "★ "}{display} <span class="count">{advertiser_counts[adv]}</span></button>\n'
    html += '    </div>\n'

    html += '    <h3>Platform</h3>\n'
    html += '    <div class="filter-group">\n'
    html += '      <button class="filter-btn active" data-filter="platform" data-value="all" onclick="setFilter(\'platform\',\'all\',this)">All Platforms <span class="count">' + str(len(all_ads)) + '</span></button>\n'
    fb_count = sum(1 for c in cards_json if c["source"] == "facebook")
    g_count = sum(1 for c in cards_json if c["source"] == "google")
    html += f'      <button class="filter-btn" data-filter="platform" data-value="facebook" onclick="setFilter(\'platform\',\'facebook\',this)">Facebook <span class="count">{fb_count}</span></button>\n'
    html += f'      <button class="filter-btn" data-filter="platform" data-value="google" onclick="setFilter(\'platform\',\'google\',this)">Google <span class="count">{g_count}</span></button>\n'
    html += '    </div>\n'

    html += '    <h3>Format</h3>\n'
    html += '    <div class="filter-group">\n'
    html += '      <button class="filter-btn active" data-filter="format" data-value="all" onclick="setFilter(\'format\',\'all\',this)">All Formats <span class="count">' + str(len(all_ads)) + '</span></button>\n'
    for fmt in formats:
        fmt_count = sum(1 for c in cards_json if c["ad_format"] == fmt)
        html += f'      <button class="filter-btn" data-filter="format" data-value="{fmt}" onclick="setFilter(\'format\',\'{fmt}\',this)">{fmt.title()} <span class="count">{fmt_count}</span></button>\n'
    html += '    </div>\n'

    html += """
  </div>

  <!-- Main Grid -->
  <div class="main">
    <div class="masonry" id="adGrid">
"""

    # Build ad cards
    for card in cards_json:
        score = card["score"]
        has_img = bool(card["img_src"])

        html += f'''      <div class="ad-card"
           data-advertiser="{card['advertiser']}"
           data-platform="{card['source']}"
           data-format="{card['ad_format']}"
           data-score="{score}"
           onclick="window.open('{card['ad_url']}','_blank')">
        <div class="card-header">
          <span class="platform-icon">{platform_icon(card['source'])}</span>
          <span class="advertiser">{card['advertiser'].replace('_',' ')}</span>
          {f'<span class="score-badge" style="background:{card["score_color"]}">{score} · {card["score_label"]}</span>' if score >= 0 else ''}
        </div>
        <div class="card-image">
          {f'<img src="{card["img_src"]}" alt="Ad creative" loading="lazy">' if has_img else '<div class="no-image">No preview available</div>'}
          <span class="format-badge">{format_icon(card["ad_format"])} {card["ad_format"].title()}</span>
          {f'<span class="versions-badge">{card["version_count"]} versions</span>' if card["has_multiple_versions"] else ''}
          {f'<div class="video-overlay"><svg width="24" height="24" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" fill="white"/></svg></div>' if card["ad_format"] == "video" else ''}
        </div>
        <div class="card-body">
          <div class="copy card-copy">{card["copy_text"][:200] if card["copy_text"] else "<em>No copy extracted</em>"}</div>
          <div class="meta-row">
            {f'<span class="tag cta">{card["cta"]}</span>' if card["cta"] else ''}
            {f'<span class="tag date">{card["start_date"]}</span>' if card["start_date"] else ''}
            {f'<span class="tag">ID: {card["library_id"]}</span>' if card["library_id"] else ''}
          </div>
        </div>
'''
        # Issues footer
        issues = card.get("issues", [])
        if issues:
            html += '        <div class="card-footer card-issues">\n'
            for issue in issues[:3]:
                sev = issue.get("severity", "low")
                html += f'          <div class="issue"><span class="issue-dot {sev}"></span>{issue.get("issue","")[:80]}</div>\n'
            html += '        </div>\n'

        # Score breakdown (shown on hover)
        cats = card.get("category_scores", {})
        if cats:
            max_scores = {"copy_quality": 25, "visual_quality": 20, "targeting_signals": 15,
                         "compliance": 15, "brand_consistency": 15, "freshness": 10}
            html += '        <div class="score-detail card-scores">\n'
            for cat_key, cat_data in cats.items():
                if isinstance(cat_data, dict):
                    val = cat_data.get("score", 0)
                    max_val = max_scores.get(cat_key, 25)
                    pct = min(100, (val / max_val) * 100) if max_val > 0 else 0
                    color = "#22c55e" if pct >= 70 else "#eab308" if pct >= 50 else "#ef4444"
                    name = cat_key.replace("_", " ").title()[:8]
                    html += f'          <div class="score-bar-row"><span class="score-bar-label">{name}</span><div class="score-bar"><div class="score-bar-fill" style="width:{pct}%;background:{color}"></div></div><span class="score-bar-val">{val}</span></div>\n'
            html += '        </div>\n'

        html += '      </div>\n'

    html += """
    </div>
  </div>
</div>

<script>
// ── State ──
let filters = { advertiser: 'all', platform: 'all', format: 'all' };
let scoreRange = 'all';
let searchQuery = '';
let showCopy = true, showIssues = true, showScores = false;

// ── Filter logic ──
function setFilter(type, value, btn) {
  filters[type] = value;
  // Update active state
  btn.parentElement.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  filterCards();
}

function setScoreFilter(range, chip) {
  scoreRange = range;
  document.querySelectorAll('.score-chip').forEach(c => c.classList.remove('active'));
  chip.classList.add('active');
  filterCards();
}

function filterCards() {
  searchQuery = document.querySelector('.search-box').value.toLowerCase();
  document.querySelectorAll('.ad-card').forEach(card => {
    const adv = card.dataset.advertiser;
    const plat = card.dataset.platform;
    const fmt = card.dataset.format;
    const score = parseInt(card.dataset.score);
    const text = card.innerText.toLowerCase();

    let show = true;
    if (filters.advertiser !== 'all' && adv !== filters.advertiser) show = false;
    if (filters.platform !== 'all' && plat !== filters.platform) show = false;
    if (filters.format !== 'all' && fmt !== filters.format) show = false;
    if (searchQuery && !text.includes(searchQuery)) show = false;

    if (scoreRange === 'good' && score < 70) show = false;
    if (scoreRange === 'ok' && (score < 50 || score >= 70)) show = false;
    if (scoreRange === 'poor' && score >= 50) show = false;

    card.classList.toggle('hidden', !show);
  });

  // Update visible count
  const visible = document.querySelectorAll('.ad-card:not(.hidden)').length;
  document.title = `TC Ads QA — ${visible} ads`;
}

// ── View toggle ──
function setView(mode, btn) {
  const grid = document.getElementById('adGrid');
  btn.parentElement.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  if (mode === 'list') {
    grid.style.columnCount = '1';
    grid.style.maxWidth = '700px';
  } else {
    grid.style.columnCount = '';
    grid.style.maxWidth = '';
  }
}

// ── Detail toggles ──
function toggleDetail(type, el) {
  el.classList.toggle('on');
  const isOn = el.classList.contains('on');
  const cls = type === 'copy' ? 'card-copy' : type === 'issues' ? 'card-issues' : 'card-scores';
  document.querySelectorAll('.' + cls).forEach(e => {
    e.style.display = isOn ? '' : 'none';
  });
  if (type === 'scores' && isOn) {
    document.querySelectorAll('.score-detail').forEach(e => e.style.display = 'block');
  }
}

// ── Insights toggle ──
function toggleInsights() {
  document.getElementById('insightsPanel').classList.toggle('visible');
}

// Init: hide score details by default
document.querySelectorAll('.score-detail').forEach(e => e.style.display = 'none');
</script>
</body>
</html>"""

    path.write_text(html)
    print(f"  Dashboard saved: {path}")
    return path
