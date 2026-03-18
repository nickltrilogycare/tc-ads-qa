"""
TC Ads QA Dashboard v2 — Premium Visual Dashboard
Modelled on Meta Ad Library + MagicBrief + Foreplay
Clean, white, professional. Grouped by advertiser. Video embedding. Support at Home focus.
"""
import base64
import json
import re
from datetime import datetime
from pathlib import Path
from datetime import timedelta
from config import REPORTS_DIR

AD_IMAGES_DIR = Path(__file__).parent.parent / "ad_images"
AD_HISTORY_PATH = Path(__file__).parent.parent / "data" / "ad_history.json"

# Support at Home keyword filter — from research agent analysis
SAH_PRIMARY = [
    "support at home", "support at home program", "support at home funding",
    "support at home classification", "replaced home care packages",
    "new aged care program",
]
SAH_SECONDARY = [
    "home care package", "self-managed home care", "self-managed aged care",
    "government-funded home care", "government-funded aged care",
    "stay at home longer", "live independently at home",
    "choose your own workers", "choose your own carers",
    "more hours of care", "aged care funding", "my aged care",
    "aged care assessment", "care management cap",
]
SAH_TERTIARY = [
    "home care", "aged care at home", "care at home", "in-home care",
    "home support", "independent living", "care in the home",
    "care hours", "care package", "funding", "self-managed",
    "home care provider", "care coordination",
]
SAH_EXCLUDE = [
    "residential aged care", "nursing home", "retirement village",
    "retirement living", "ndis", "disability",
]


def is_sah_relevant(ad: dict) -> bool:
    """Check if an ad is relevant to Support at Home using tiered keyword matching."""
    text = (ad.get("copy_text", "") + " " + ad.get("full_text", "")).lower()

    # Exclude residential/NDIS unless also mentioning home care
    if any(ex in text for ex in SAH_EXCLUDE):
        if not any(kw in text for kw in SAH_PRIMARY + SAH_SECONDARY):
            return False

    # Primary keywords = definite match
    if any(kw in text for kw in SAH_PRIMARY):
        return True
    # Secondary = strong match
    if any(kw in text for kw in SAH_SECONDARY):
        return True
    # Tertiary = need at least 2 matches
    matches = sum(1 for kw in SAH_TERTIARY if kw in text)
    return matches >= 2


def image_to_base64(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    suffix = p.suffix.lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "gif": "image/gif", "webp": "image/webp"}.get(suffix.lstrip("."), "image/png")
    try:
        data = p.read_bytes()
        return f"data:{mime};base64,{base64.b64encode(data).decode()}"
    except Exception:
        return ""


def get_image_src(ad: dict) -> str:
    el_ss = ad.get("element_screenshot")
    if el_ss:
        b64 = image_to_base64(el_ss)
        if b64:
            return b64
    for path in ad.get("image_paths", []):
        if path.startswith("/"):
            b64 = image_to_base64(path)
            if b64:
                return b64
        elif path.startswith("http"):
            return path
    for url in ad.get("image_urls", []):
        if url.startswith("http"):
            return url
    return ""


def get_fb_embed_url(ad: dict) -> str:
    """Generate Facebook Ad Library embed URL for iframe."""
    lid = ad.get("library_id", "")
    if lid:
        return f"https://www.facebook.com/ads/library/?id={lid}"
    return ad.get("ad_url", "#")


def generate_dashboard_v2(
    all_ads: list[dict],
    analysis_results: list[dict],
    competitive_analysis: dict,
    sah_only: bool = True,
) -> Path:
    now = datetime.now()
    filename = f"ads_dashboard_{now:%Y%m%d_%H%M}.html"
    path = REPORTS_DIR / filename

    # Load ad history for freshness badges
    ad_history = {}
    if AD_HISTORY_PATH.exists():
        try:
            ad_history = json.loads(AD_HISTORY_PATH.read_text())
        except Exception:
            pass

    def compute_freshness(library_id: str, start_date: str) -> str:
        """Return 'new' (0-7 days), 'recent' (8-30), or 'stale' (31+)."""
        first_seen = None
        if library_id and library_id in ad_history:
            fs = ad_history[library_id].get("first_seen", "")
            if fs:
                try:
                    first_seen = datetime.strptime(fs, "%Y-%m-%d")
                except Exception:
                    pass
        if first_seen is None and start_date:
            try:
                first_seen = datetime.strptime(start_date, "%Y-%m-%d")
            except Exception:
                pass
        if first_seen is None:
            return "recent"  # unknown = default to recent (no badge)
        days = (now - first_seen).days
        if days <= 7:
            return "new"
        elif days <= 30:
            return "recent"
        else:
            return "stale"

    # Filter for SAH if requested
    if sah_only:
        filtered = [a for a in all_ads if is_sah_relevant(a)]
        if len(filtered) < 5:
            # If too few SAH matches, include all (the keywords might not match scraped text well)
            filtered = all_ads
        all_ads = filtered

    # Build score lookup
    score_map = {}
    for r in analysis_results:
        src = r.get("source_ad", {})
        key = f"{src.get('source', '')}_{src.get('advertiser', '')}_{src.get('ad_index', '')}"
        score_map[key] = r

    # Group ads by advertiser
    by_advertiser = {}
    for ad in all_ads:
        adv = ad.get("advertiser", "Unknown").replace("_", " ")
        # Normalize names
        if "trilogy" in adv.lower():
            adv = "Trilogy Care"
        elif "bolton" in adv.lower():
            adv = "Bolton Clarke"
        elif "hammond" in adv.lower():
            adv = "HammondCare"
        elif "just" in adv.lower() and "better" in adv.lower():
            adv = "Just Better Care"
        elif "dovida" in adv.lower() or "home instead" in adv.lower():
            adv = "Dovida"
        elif "kincare" in adv.lower() or "silverchain" in adv.lower():
            adv = "KinCare"
        elif "homemade" in adv.lower():
            adv = "HomeMade"
        by_advertiser.setdefault(adv, []).append(ad)

    # Ensure Trilogy is first
    advertiser_order = ["Trilogy Care"] + sorted(k for k in by_advertiser if k != "Trilogy Care")

    # Build cards
    cards = []
    for ad in all_ads:
        key = f"{ad.get('source', '')}_{ad.get('advertiser', '')}_{ad.get('ad_index', '')}"
        analysis = score_map.get(key, {})
        score = analysis.get("overall_score", -1)
        img = get_image_src(ad)
        adv = ad.get("advertiser", "Unknown").replace("_", " ")
        if "trilogy" in adv.lower(): adv = "Trilogy Care"
        elif "bolton" in adv.lower(): adv = "Bolton Clarke"
        elif "hammond" in adv.lower(): adv = "HammondCare"
        elif "just" in adv.lower() and "better" in adv.lower(): adv = "Just Better Care"
        elif "dovida" in adv.lower() or "home instead" in adv.lower(): adv = "Dovida"
        elif "kincare" in adv.lower() or "silverchain" in adv.lower(): adv = "KinCare"
        elif "homemade" in adv.lower(): adv = "HomeMade"

        lid = ad.get("library_id", "")
        freshness = compute_freshness(lid, ad.get("start_date", ""))

        cards.append({
            "advertiser": adv,
            "source": ad.get("source", "unknown"),
            "format": ad.get("ad_format", "image"),
            "ad_url": ad.get("ad_url", "#"),
            "library_id": lid,
            "start_date": ad.get("start_date", ""),
            "copy": (ad.get("copy_text") or ad.get("full_text", ""))[:400],
            "cta": ad.get("cta") or analysis.get("cta_identified", ""),
            "score": score,
            "img": img,
            "versions": ad.get("version_count", 1),
            "issues": analysis.get("issues", []),
            "strengths": analysis.get("strengths", []),
            "cats": analysis.get("category_scores", {}),
            "freshness": freshness,
        })

    # Stats
    trilogy_cards = [c for c in cards if c["advertiser"] == "Trilogy Care"]
    trilogy_scores = [c["score"] for c in trilogy_cards if c["score"] >= 0]
    avg = round(sum(trilogy_scores) / len(trilogy_scores), 1) if trilogy_scores else 0

    exec_summary = competitive_analysis.get("executive_summary", "")
    recs = competitive_analysis.get("recommendations", [])
    strengths = competitive_analysis.get("trilogy_strengths", [])
    weaknesses = competitive_analysis.get("trilogy_weaknesses", [])

    # ── BUILD HTML ──
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TC Ads QA — Support at Home</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
/* ═══════════════════════════════════════
   Design System — Meta Ad Library inspired
   Clean white, generous whitespace, Inter font
   ═══════════════════════════════════════ */
:root {{
  --bg: #F0F2F5;
  --white: #FFFFFF;
  --card: #FFFFFF;
  --border: #DADDE1;
  --border-light: #E4E6EB;
  --text: #1C1E21;
  --text-secondary: #65676B;
  --text-tertiary: #8A8D91;
  --accent: #1877F2;
  --accent-hover: #166FE5;
  --green: #31A24C;
  --yellow: #F7B928;
  --red: #E4405F;
  --orange: #F5793B;
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.1);
  --shadow-md: 0 2px 12px rgba(0,0,0,0.1);
  --shadow-lg: 0 8px 30px rgba(0,0,0,0.12);
  --radius: 8px;
  --radius-lg: 12px;
  --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: var(--font); background: var(--bg); color: var(--text);
       -webkit-font-smoothing: antialiased; }}

/* ── Header ── */
.header {{
  background: var(--white); border-bottom: 1px solid var(--border);
  padding: 0 24px; position: sticky; top: 0; z-index: 100;
}}
.header-inner {{
  max-width: 1400px; margin: 0 auto;
  display: flex; align-items: center; height: 56px; gap: 16px;
}}
.header-logo {{
  display: flex; align-items: center; gap: 10px;
  font-size: 16px; font-weight: 700; color: var(--text);
  text-decoration: none;
}}
.header-logo svg {{ color: var(--accent); }}
.header-nav {{
  display: flex; gap: 4px; margin-left: 32px;
}}
.header-nav button {{
  padding: 8px 16px; border: none; border-radius: 6px;
  font-family: var(--font); font-size: 14px; font-weight: 500;
  cursor: pointer; transition: all 0.15s;
  background: transparent; color: var(--text-secondary);
}}
.header-nav button:hover {{ background: var(--bg); }}
.header-nav button.active {{
  background: #E7F3FF; color: var(--accent); font-weight: 600;
}}
.header-meta {{
  margin-left: auto; font-size: 13px; color: var(--text-tertiary);
}}

/* ── Toolbar ── */
.toolbar {{
  background: var(--white); border-bottom: 1px solid var(--border);
  padding: 12px 24px;
}}
.toolbar-inner {{
  max-width: 1400px; margin: 0 auto;
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
}}
.filter-chip {{
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 12px; border: 1px solid var(--border);
  border-radius: 20px; font-size: 13px; font-weight: 500;
  cursor: pointer; background: var(--white); color: var(--text);
  transition: all 0.15s; user-select: none;
}}
.filter-chip:hover {{ border-color: var(--text-tertiary); }}
.filter-chip.active {{
  background: var(--accent); color: white; border-color: var(--accent);
}}
.filter-chip .dot {{
  width: 8px; height: 8px; border-radius: 50%;
}}
.search-input {{
  flex: 1; min-width: 200px; max-width: 360px;
  padding: 8px 12px 8px 36px; border: 1px solid var(--border);
  border-radius: 20px; font-size: 14px; font-family: var(--font);
  background: var(--bg); color: var(--text); outline: none;
  transition: border-color 0.15s;
}}
.search-input:focus {{ border-color: var(--accent); background: var(--white); }}
.search-wrap {{
  position: relative; flex: 1; min-width: 200px; max-width: 360px;
}}
.search-wrap svg {{
  position: absolute; left: 12px; top: 50%; transform: translateY(-50%);
  color: var(--text-tertiary);
}}
.view-btns {{
  display: flex; gap: 2px; margin-left: auto;
  background: var(--bg); border-radius: 6px; padding: 2px;
}}
.view-btn {{
  padding: 6px 10px; border: none; border-radius: 4px;
  background: transparent; cursor: pointer; color: var(--text-tertiary);
  display: flex; align-items: center; transition: all 0.15s;
}}
.view-btn.active {{ background: var(--white); color: var(--text); box-shadow: var(--shadow-sm); }}
.sort-select {{
  padding: 6px 28px 6px 12px; border: 1px solid var(--border);
  border-radius: 20px; font-size: 13px; font-weight: 500;
  font-family: var(--font); background: var(--white); color: var(--text);
  cursor: pointer; outline: none; appearance: none;
  -webkit-appearance: none; -moz-appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg width='10' height='6' viewBox='0 0 10 6' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%2365676B' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 10px center;
  transition: border-color 0.15s;
}}
.sort-select:hover {{ border-color: var(--text-tertiary); }}
.sort-select:focus {{ border-color: var(--accent); }}

/* ── Stats Strip ── */
.stats {{
  max-width: 1400px; margin: 16px auto; padding: 0 24px;
  display: flex; gap: 12px; flex-wrap: wrap;
}}
.stat-card {{
  background: var(--white); border: 1px solid var(--border-light);
  border-radius: var(--radius); padding: 14px 20px;
  flex: 1; min-width: 130px;
}}
.stat-card .val {{ font-size: 24px; font-weight: 700; }}
.stat-card .lbl {{ font-size: 12px; color: var(--text-tertiary); margin-top: 2px; font-weight: 500; }}

/* ── Main Content ── */
.content {{
  max-width: 1400px; margin: 0 auto; padding: 0 24px 40px;
}}

/* ── Advertiser Section ── */
.advertiser-section {{
  margin-top: 24px;
}}
.advertiser-header {{
  display: flex; align-items: center; gap: 12px;
  padding: 12px 0; border-bottom: 1px solid var(--border-light);
  margin-bottom: 16px;
}}
.advertiser-header h2 {{
  font-size: 18px; font-weight: 700;
}}
.advertiser-header .badge {{
  padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;
}}
.badge-trilogy {{ background: #E7F3FF; color: var(--accent); }}
.badge-competitor {{ background: #F0F2F5; color: var(--text-secondary); }}
.advertiser-header .count {{
  margin-left: auto; font-size: 13px; color: var(--text-tertiary);
}}

/* ── Ad Grid ── */
.ad-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}}
.ad-grid.list-view {{
  grid-template-columns: 1fr;
  max-width: 680px;
}}

/* ── Ad Card — Meta Ad Library style ── */
.ad-card {{
  background: var(--card); border: 1px solid var(--border-light);
  border-radius: var(--radius-lg); overflow: hidden;
  transition: box-shadow 0.2s, transform 0.15s;
}}
.ad-card:hover {{
  box-shadow: var(--shadow-lg);
  transform: translateY(-1px);
}}
.ad-card.hidden {{ display: none; }}

/* Card: Meta line */
.card-meta {{
  display: flex; align-items: center; gap: 8px;
  padding: 12px 16px 8px;
}}
.card-meta .platform {{
  width: 32px; height: 32px; border-radius: 50%;
  background: var(--bg); display: flex; align-items: center; justify-content: center;
}}
.card-meta .info {{ flex: 1; }}
.card-meta .name {{ font-size: 14px; font-weight: 600; }}
.card-meta .sub {{ font-size: 12px; color: var(--text-tertiary); }}
.card-meta .score-pill {{
  padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 700;
  color: white;
}}

/* Card: Creative */
.card-creative {{
  position: relative; background: #F8F9FA;
  cursor: pointer;
}}
.card-creative img {{
  width: 100%; display: block;
  max-height: 400px; object-fit: contain;
  background: #F8F9FA;
}}
.card-creative .no-preview {{
  height: 180px; display: flex; align-items: center; justify-content: center;
  color: var(--text-tertiary); font-size: 13px;
}}
.card-creative .format-pill {{
  position: absolute; top: 8px; right: 8px;
  background: rgba(0,0,0,0.6); color: white;
  padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;
  display: flex; align-items: center; gap: 4px;
  backdrop-filter: blur(4px);
}}
.card-creative .play-btn {{
  position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
  width: 56px; height: 56px; border-radius: 50%;
  background: rgba(0,0,0,0.5); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  transition: background 0.2s;
}}
.card-creative:hover .play-btn {{ background: rgba(0,0,0,0.7); }}
.card-creative .versions {{
  position: absolute; bottom: 8px; right: 8px;
  background: var(--accent); color: white;
  padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;
}}

/* Card: Copy */
.card-copy {{
  padding: 12px 16px;
}}
.card-copy p {{
  font-size: 14px; line-height: 1.5; color: var(--text);
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;
  overflow: hidden;
}}
.card-copy .tags {{
  display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px;
}}
.card-copy .tag {{
  padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 500;
}}
.tag-cta {{ background: #E7F3FF; color: var(--accent); }}
.tag-date {{ background: #F0F2F5; color: var(--text-secondary); }}
.tag-id {{ background: #F0F2F5; color: var(--text-tertiary); font-family: monospace; }}

/* Card: Score Detail (expandable) */
.card-detail {{
  border-top: 1px solid var(--border-light); padding: 12px 16px;
  display: none;
}}
.ad-card.expanded .card-detail {{ display: block; }}
.score-row {{
  display: flex; align-items: center; gap: 8px; margin: 4px 0;
}}
.score-row .lbl {{ width: 80px; font-size: 11px; color: var(--text-tertiary); text-align: right; }}
.score-bar {{ flex: 1; height: 4px; background: var(--border-light); border-radius: 2px; }}
.score-bar-fill {{ height: 100%; border-radius: 2px; }}
.score-row .val {{ width: 24px; font-size: 11px; font-weight: 600; }}

.issues-list {{ margin-top: 8px; }}
.issue-item {{
  display: flex; align-items: start; gap: 6px;
  font-size: 12px; color: var(--text-secondary); margin: 4px 0;
}}
.issue-dot {{ width: 6px; height: 6px; border-radius: 50%; margin-top: 5px; flex-shrink: 0; }}

/* Card: Footer */
.card-footer {{
  display: flex; align-items: center; padding: 8px 16px 12px;
  gap: 8px;
}}
.card-footer button {{
  padding: 6px 12px; border: 1px solid var(--border);
  border-radius: 6px; font-size: 12px; font-weight: 500;
  cursor: pointer; background: var(--white); color: var(--text);
  font-family: var(--font); transition: all 0.15s;
}}
.card-footer button:hover {{ background: var(--bg); }}
.card-footer .btn-primary {{
  background: var(--accent); color: white; border-color: var(--accent);
}}
.card-footer .btn-primary:hover {{ background: var(--accent-hover); }}

/* ── Insights Drawer ── */
.drawer-overlay {{
  display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  z-index: 200;
}}
.drawer-overlay.open {{ display: block; }}
.drawer {{
  position: fixed; top: 0; right: -480px; width: 480px; height: 100vh;
  background: var(--white); z-index: 201; overflow-y: auto;
  box-shadow: -4px 0 24px rgba(0,0,0,0.15);
  transition: right 0.3s ease;
  padding: 24px;
}}
.drawer.open {{ right: 0; }}
.drawer h2 {{ font-size: 18px; margin-bottom: 16px; }}
.drawer h3 {{ font-size: 14px; color: var(--text-secondary); margin: 16px 0 8px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
.drawer .insight-item {{
  padding: 8px 0; border-bottom: 1px solid var(--border-light);
  font-size: 14px; line-height: 1.5;
}}
.drawer .rec-item {{
  display: flex; align-items: start; gap: 8px; padding: 8px 0;
  border-bottom: 1px solid var(--border-light);
}}
.rec-dot {{ width: 8px; height: 8px; border-radius: 50%; margin-top: 6px; flex-shrink: 0; }}
.drawer .close-btn {{
  position: absolute; top: 16px; right: 16px;
  width: 32px; height: 32px; border-radius: 50%;
  border: none; background: var(--bg); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}}

/* ── Score Logic Panel ── */
.score-logic {{
  background: var(--white); border: 1px solid var(--border-light);
  border-radius: var(--radius-lg); padding: 20px; margin-top: 24px;
  display: none;
}}
.score-logic.visible {{ display: block; }}
.score-logic h3 {{ font-size: 16px; margin-bottom: 12px; }}
.score-logic table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
.score-logic th {{ text-align: left; padding: 8px; border-bottom: 2px solid var(--border); font-weight: 600; color: var(--text-secondary); }}
.score-logic td {{ padding: 8px; border-bottom: 1px solid var(--border-light); }}
.score-logic .weight {{ font-weight: 700; color: var(--accent); }}

/* ── Freshness Badges ── */
.freshness-badge {{
  padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 700;
  letter-spacing: 0.3px; text-transform: uppercase; margin-left: auto;
}}
.badge-new {{ background: #E8F5E9; color: #31A24C; }}
.badge-stale {{ background: #F0F2F5; color: #8A8D91; }}

/* ── Issues-First Chip (visible on cards scoring <70) ── */
.card-issue-preview {{
  padding: 6px 16px 4px; display: flex; align-items: center; gap: 6px;
}}
.issue-chip {{
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 500;
  background: #FFF0F0; color: var(--red); max-width: 100%;
}}
.issue-chip .issue-chip-dot {{
  width: 6px; height: 6px; border-radius: 50%; background: var(--red); flex-shrink: 0;
}}
.issue-chip-text {{
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}}

/* ── Gallery View ── */
.ad-grid.gallery-view {{
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 8px;
}}
.ad-grid.gallery-view .ad-card {{
  border-radius: var(--radius);
}}
.ad-grid.gallery-view .card-meta,
.ad-grid.gallery-view .card-copy,
.ad-grid.gallery-view .card-footer,
.ad-grid.gallery-view .card-detail,
.ad-grid.gallery-view .card-issue-preview {{
  display: none;
}}
.ad-grid.gallery-view .card-creative {{
  position: relative;
}}
.ad-grid.gallery-view .card-creative img {{
  max-height: 260px; object-fit: cover;
}}
.gallery-overlay {{
  position: absolute; bottom: 0; left: 0; right: 0;
  background: linear-gradient(transparent, rgba(0,0,0,0.75));
  color: white; padding: 24px 10px 8px; font-size: 12px;
  opacity: 0; transition: opacity 0.2s;
  pointer-events: none;
}}
.gallery-overlay .g-name {{ font-weight: 600; }}
.gallery-overlay .g-score {{
  display: inline-block; padding: 1px 6px; border-radius: 8px;
  font-size: 11px; font-weight: 700; margin-left: 4px;
}}
.ad-grid.gallery-view .ad-card:hover .gallery-overlay {{
  opacity: 1;
}}

/* ── Dark Mode ── */
body.dark-mode {{
  --bg: #1a1a2e; --white: #16213e; --card: #1a1d2e; --border: #2d3148;
  --border-light: #2d3148; --text: #e4e6f0; --text-secondary: #8b8fa3;
  --text-tertiary: #6b7080; --accent: #6366f1;
}}
body.dark-mode .header {{ background: #16213e; border-color: #2d3148; }}
body.dark-mode .toolbar {{ background: #16213e; border-color: #2d3148; }}
body.dark-mode .ad-card {{ background: #1a1d2e; border-color: #2d3148; }}
body.dark-mode .ad-card:hover {{ box-shadow: 0 8px 24px rgba(0,0,0,0.4); }}
body.dark-mode .card-creative {{ background: #232736; }}
body.dark-mode .stat-card {{ background: #1a1d2e; border-color: #2d3148; }}
body.dark-mode .score-logic {{ background: #1a1d2e; border-color: #2d3148; }}
body.dark-mode .drawer {{ background: #16213e; }}
body.dark-mode .filter-chip {{ background: #1a1d2e; border-color: #2d3148; color: #e4e6f0; }}
body.dark-mode .search-input {{ background: #1a1d2e; border-color: #2d3148; color: #e4e6f0; }}

/* ── Mobile hamburger ── */
.mobile-menu-btn {{
  display: none; align-items: center; justify-content: center;
  width: 36px; height: 36px; border: 1px solid var(--border); border-radius: 6px;
  background: var(--white); cursor: pointer; padding: 0;
}}
.mobile-menu-btn svg {{ color: var(--text); }}

/* ── Responsive ── */
@media (max-width: 768px) {{
  .ad-grid {{ grid-template-columns: 1fr; }}
  .ad-grid.gallery-view {{ grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); }}
  .header-nav {{ display: none; flex-direction: column; position: absolute; top: 56px; left: 0; right: 0; background: white; padding: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); z-index: 101; }}
  .header-nav.open {{ display: flex; }}
  .mobile-menu-btn {{ display: flex; }}
  .stats {{ flex-direction: column; }}
  .drawer {{ width: 100%; right: -100%; }}
}}
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div class="header-inner">
    <a class="header-logo" href="#">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 3v18"/></svg>
      TC Ads QA
    </a>
    <button class="mobile-menu-btn" onclick="document.querySelector('.header-nav').classList.toggle('open')" aria-label="Menu">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
    </button>
    <div class="header-nav">
      <button class="active" onclick="setTab('all',this)">All Ads</button>
      <button onclick="setTab('trilogy',this)">Trilogy Care</button>
      <button onclick="setTab('competitors',this)">Competitors</button>
      <button onclick="toggleScoreLogic()">Score Logic</button>
      <button onclick="toggleMarketVoice()">Market Voice</button>
      <button onclick="toggleGapMatrix()">Gap Matrix</button>
      <button onclick="toggleVolumeTracker()">Volume</button>
      <button onclick="toggleActionQueue()">Actions</button>
      <button onclick="openDrawer()">Insights</button>
      <button onclick="openBoardsDrawer()">Swipe File</button>
      <button onclick="toggleExecView()" style="background:#1877F2;color:white;border-radius:6px;">CMO Brief</button>
    </div>
    <span class="header-meta">{now:%d %B %Y} · Support at Home</span>
    <button onclick="toggleDarkMode()" style="width:32px;height:32px;border:1px solid var(--border);border-radius:6px;background:var(--white);cursor:pointer;font-size:16px;" title="Toggle dark mode" id="darkModeBtn">🌙</button>
  </div>
</div>

<!-- Toolbar -->
<div class="toolbar">
  <div class="toolbar-inner">
    <div class="search-wrap">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
      <input type="text" class="search-input" placeholder="Search ads by copy, CTA, or advertiser..." oninput="filterAds()">
    </div>

    <div class="filter-chip active" data-filter="platform" data-val="all" onclick="toggleFilter(this)">
      All Platforms
    </div>
    <div class="filter-chip" data-filter="platform" data-val="facebook" onclick="toggleFilter(this)">
      <span class="dot" style="background:#1877F2"></span> Facebook
    </div>
    <div class="filter-chip" data-filter="platform" data-val="google" onclick="toggleFilter(this)">
      <span class="dot" style="background:#4285F4"></span> Google
    </div>

    <div class="filter-chip" data-filter="format" data-val="video" onclick="toggleFilter(this)">
      Video
    </div>
    <div class="filter-chip" data-filter="format" data-val="image" onclick="toggleFilter(this)">
      Image
    </div>
    <div class="filter-chip" data-filter="format" data-val="text" onclick="toggleFilter(this)">
      Text
    </div>

    <div class="filter-chip" data-filter="score" data-val="poor" onclick="toggleFilter(this)" style="border-color:var(--red);color:var(--red)">
      Poor &lt;50
    </div>

    <div class="filter-chip" data-filter="freshness" data-val="new" onclick="toggleFilter(this)" style="border-color:#31A24C;color:#31A24C">
      New This Week
    </div>

    <select class="sort-select" onchange="sortAds(this.value)">
      <option value="default">Sort: Default</option>
      <option value="score_desc">Score (High→Low)</option>
      <option value="score_asc">Score (Low→High)</option>
      <option value="newest">Newest First</option>
      <option value="oldest">Oldest First</option>
    </select>

    <div class="view-btns">
      <button class="view-btn active" onclick="setView('grid',this)" title="Grid view">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M3 3h8v8H3V3zm10 0h8v8h-8V3zM3 13h8v8H3v-8zm10 0h8v8h-8v-8z"/></svg>
      </button>
      <button class="view-btn" onclick="setView('list',this)" title="List view">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M3 4h18v2H3V4zm0 7h18v2H3v-2zm0 7h18v2H3v-2z"/></svg>
      </button>
      <button class="view-btn" onclick="setView('gallery',this)" title="Gallery view">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M3 3h7v7H3V3zm11 0h7v7h-7V3zM3 14h7v7H3v-7zm11 0h7v7h-7v-7z"/></svg>
      </button>
    </div>
  </div>
</div>

<!-- Stats -->
<div class="stats">
  <div class="stat-card">
    <div class="val">{len(cards)}</div>
    <div class="lbl">Total Ads</div>
  </div>
  <div class="stat-card">
    <div class="val">{len(trilogy_cards)}</div>
    <div class="lbl">Trilogy Care</div>
  </div>
  <div class="stat-card">
    <div class="val">{len(cards) - len(trilogy_cards)}</div>
    <div class="lbl">Competitors</div>
  </div>
  <div class="stat-card">
    <div class="val" style="color:{'var(--green)' if avg >= 70 else 'var(--orange)' if avg >= 50 else 'var(--red)'}">{avg}</div>
    <div class="lbl">Avg Trilogy Score</div>
  </div>
  <div class="stat-card">
    <div class="val">{len(advertiser_order) - 1}</div>
    <div class="lbl">Competitors Tracked</div>
  </div>
</div>

<!-- Score Logic Panel -->
<div class="content">
"""

    # ── Executive View ──
    try:
        from reports.executive_view import get_executive_view_html, get_executive_view_css
        # Load gaps if available
        try:
            msg_gaps = json.loads((Path(__file__).parent.parent / "data" / "messaging_gaps.json").read_text())
        except Exception:
            msg_gaps = None
        html += f"<style>{get_executive_view_css()}</style>"
        html += get_executive_view_html(cards, competitive_analysis, msg_gaps)
    except Exception as e:
        html += f"<!-- Exec view failed: {e} -->"

    html += """
<div class="score-logic" id="scoreLogic">
  <h3>Quality Score Methodology</h3>
  <p style="font-size:14px;color:var(--text-secondary);margin-bottom:16px;">
    Each ad is scored out of 100 by AI analysis (GPT-4.1) across 6 categories weighted for aged care advertising effectiveness.
  </p>
  <table>
    <tr><th>Category</th><th>Weight</th><th>What It Measures</th></tr>
    <tr><td>Copy Quality</td><td class="weight">25 pts</td><td>Clarity, persuasion, emotional resonance, grammar, CTA strength. For aged care: empathy, dignity, trust signals.</td></tr>
    <tr><td>Visual Quality</td><td class="weight">20 pts</td><td>Design professionalism, brand alignment, image quality and relevance to aged care.</td></tr>
    <tr><td>Targeting Signals</td><td class="weight">15 pts</td><td>Does the ad speak to the right audience? Older Australians, adult children making decisions, carers.</td></tr>
    <tr><td>Compliance</td><td class="weight">15 pts</td><td>Aged care advertising regulations, no misleading claims, ACQSC alignment, appropriate imagery.</td></tr>
    <tr><td>Brand Consistency</td><td class="weight">15 pts</td><td>Alignment with brand voice — for Trilogy: self-managed, empowerment, independence, transparent fees.</td></tr>
    <tr><td>Freshness</td><td class="weight">10 pts</td><td>Is the ad current and timely? References to Support at Home, recent policy changes.</td></tr>
  </table>
  <div style="margin-top:16px;display:flex;gap:16px;">
    <div><span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:var(--green);margin-right:4px;vertical-align:middle;"></span> <strong>70-100</strong> Good</div>
    <div><span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:var(--yellow);margin-right:4px;vertical-align:middle;"></span> <strong>50-69</strong> Needs Work</div>
    <div><span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:var(--red);margin-right:4px;vertical-align:middle;"></span> <strong>&lt;50</strong> Poor</div>
  </div>
</div>
"""

    # ── Market Voice Share Panel ──
    try:
        msg_data = json.loads((Path(__file__).parent.parent / "data" / "messaging_analysis.json").read_text())
        msg_dist = msg_data.get("messaging_distribution", {})
        msg_trilogy = msg_data.get("trilogy_share", {})

        from reports.charts import market_voice_share_svg
        voice_svg = market_voice_share_svg(msg_dist, msg_trilogy)

        # Find gaps — angles with low Trilogy share
        gaps = []
        for angle, count in sorted(msg_dist.items(), key=lambda x: -x[1]):
            ts = msg_trilogy.get(angle, 0)
            if ts < 30 and count >= 3:
                label = angle.replace("_", " ").title()
                gaps.append(f"<li><strong>{label}</strong> — {count} competitor ads, Trilogy at {ts}% share</li>")

        html += f"""
<div class="score-logic" id="marketVoice" style="margin-top:24px;">
  <h3>Market Voice Share — Messaging Intelligence</h3>
  <p style="font-size:14px;color:var(--text-secondary);margin-bottom:16px;">
    Which messaging angles dominate Support at Home advertising? Coloured bars show Trilogy Care's share within each theme. Based on {msg_data.get('sample_size', 0)} ads analyzed.
  </p>
  {voice_svg}
  {"<h4 style='margin-top:20px;font-size:14px;color:var(--red);'>Messaging Gaps (Trilogy under-represented)</h4><ul style='font-size:13px;line-height:1.8;'>" + "".join(gaps) + "</ul>" if gaps else ""}
</div>
"""
    except Exception as e:
        html += f"<!-- Market Voice Share unavailable: {e} -->\n"

    # ── Messaging Gap Heatmap Panel ──
    try:
        gap_data = json.loads((Path(__file__).parent.parent / "data" / "messaging_gaps.json").read_text())
        from reports.charts import messaging_gap_heatmap_svg

        # Normalize advertiser names in matrix
        raw_matrix = gap_data.get("matrix", {}).get("matrix", {})
        norm_matrix = {}
        for angle, advs in raw_matrix.items():
            norm = {}
            for adv, count in advs.items():
                # Normalize name
                n = adv
                if "trilogy" in adv.lower(): n = "Trilogy Care"
                elif "bolton" in adv.lower(): n = "Bolton Clarke"
                elif "dovida" in adv.lower() or "home_instead" in adv.lower(): n = "Dovida"
                elif "hammond" in adv.lower(): n = "HammondCare"
                elif "baptist" in adv.lower(): n = "BaptistCare"
                elif "anglicare" in adv.lower(): n = "Anglicare"
                elif "feros" in adv.lower(): n = "Feros Care"
                elif "prestige" in adv.lower(): n = "Prestige"
                elif "uniting" in adv.lower(): n = "Uniting"
                elif "catholic" in adv.lower(): n = "Catholic HC"
                elif "benetas" in adv.lower(): n = "Benetas"
                elif "southern" in adv.lower(): n = "Southern Cross"
                elif "australian" in adv.lower(): n = "AU Unity"
                norm[n] = norm.get(n, 0) + count
            norm_matrix[angle] = norm

        heatmap_svg = messaging_gap_heatmap_svg({"matrix": norm_matrix})

        # Gap alerts
        gap_alerts = gap_data.get("gaps", {}).get("gaps", [])
        gap_html = ""
        if gap_alerts:
            gap_html = "<h4 style='margin-top:16px;color:var(--red);font-size:14px;'>Gap Alerts</h4><ul style='font-size:13px;'>"
            for g in gap_alerts[:5]:
                gap_html += f"<li><strong>{g['angle'].replace('_',' ').title()}</strong> — {g['competitor_count']} competitor ads, 0 Trilogy</li>"
            gap_html += "</ul>"

        # ── Fill This Gap — Pre-generated Creative Briefs ──
        fill_gap_html = ""
        try:
            briefs_path = Path(__file__).parent.parent / "data" / "gap_briefs.json"
            if briefs_path.exists():
                gap_briefs = json.loads(briefs_path.read_text())
                if gap_briefs:
                    fill_gap_html = """
<div style="margin-top:28px;">
  <h4 style="color:#1a1a2e;font-size:15px;margin-bottom:4px;">
    <span style="color:var(--red);font-size:18px;">&#9679;</span> Fill This Gap — Creative Brief Generator
  </h4>
  <p style="font-size:13px;color:var(--text-secondary);margin-bottom:16px;">
    Click a gap card to expand a pre-generated creative brief. These are your biggest messaging opportunities.
  </p>
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px;">
"""
                    for idx, brief in enumerate(gap_briefs):
                        angle_name = brief.get("gap_angle", "").replace("_", " ").title()
                        comp_count = brief.get("competitor_count", 0)
                        tc_count = brief.get("trilogy_count", 0)
                        tc_share = brief.get("trilogy_share", 0)
                        sample_copy = brief.get("sample_competitor_copy", "")
                        brief_title = brief.get("brief_title", "Creative Brief")
                        objective = brief.get("objective", "")
                        key_msg = brief.get("key_message", "")
                        supporting = brief.get("supporting_messages", [])
                        tone = brief.get("tone", "")
                        fmt_rec = brief.get("format_recommendation", "")
                        headlines = brief.get("headline_options", [])
                        body_draft = brief.get("body_copy_draft", "")
                        cta = brief.get("cta", "")
                        visual = brief.get("visual_direction", "")
                        what_keep = brief.get("what_to_keep", "")
                        what_change = brief.get("what_to_change", "")
                        platform = brief.get("platform", "")

                        supporting_html = "".join(f"<li>{s}</li>" for s in supporting)
                        headlines_html = "".join(f"<li style='font-weight:600;'>{h}</li>" for h in headlines)

                        # Urgency indicator based on share
                        if tc_share < 5:
                            urgency = "CRITICAL"
                            urgency_color = "#D32F2F"
                        elif tc_share < 15:
                            urgency = "HIGH"
                            urgency_color = "#E65100"
                        else:
                            urgency = "MEDIUM"
                            urgency_color = "#F9A825"

                        fill_gap_html += f"""
    <div style="background:#fff;border:1px solid #e0e0e0;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
      <div onclick="document.getElementById('brief-{idx}').style.display=document.getElementById('brief-{idx}').style.display==='none'?'block':'none';this.querySelector('.chevron').textContent=document.getElementById('brief-{idx}').style.display==='none'?'&#9654;':'&#9660;'"
           style="padding:16px 20px;cursor:pointer;display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#fafafa,#f5f5f5);">
        <div>
          <div style="font-size:15px;font-weight:700;color:#1a1a2e;margin-bottom:4px;">{angle_name}</div>
          <div style="font-size:12px;color:var(--text-secondary);">
            <span style="background:{urgency_color};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;margin-right:8px;">{urgency}</span>
            {comp_count} competitor ads &middot; {tc_count} Trilogy &middot; {tc_share}% share
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:10px;">
          <span style="background:#1a1a2e;color:#fff;padding:6px 14px;border-radius:8px;font-size:12px;font-weight:600;">Generate Brief</span>
          <span class="chevron" style="font-size:14px;color:#666;">&#9654;</span>
        </div>
      </div>
      <div id="brief-{idx}" style="display:none;padding:0 20px 20px;">
        <div style="padding:12px 0;border-bottom:1px solid #eee;">
          <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#999;margin-bottom:4px;">Competitor Sample Copy</div>
          <div style="font-size:13px;color:#555;font-style:italic;background:#f9f9f9;padding:10px 14px;border-radius:8px;border-left:3px solid #ccc;">{sample_copy}</div>
        </div>
        <div style="padding:12px 0;border-bottom:1px solid #eee;">
          <div style="font-size:16px;font-weight:700;color:#1a1a2e;margin-bottom:6px;">{brief_title}</div>
          <div style="font-size:13px;color:#555;">{objective}</div>
        </div>
        <div style="padding:12px 0;border-bottom:1px solid #eee;">
          <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#999;margin-bottom:4px;">Key Message</div>
          <div style="font-size:14px;font-weight:600;color:#1a1a2e;">{key_msg}</div>
        </div>
        <div style="padding:12px 0;border-bottom:1px solid #eee;">
          <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#999;margin-bottom:4px;">Supporting Messages</div>
          <ul style="font-size:13px;color:#555;margin:4px 0;padding-left:18px;">{supporting_html}</ul>
        </div>
        <div style="padding:12px 0;border-bottom:1px solid #eee;">
          <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#999;margin-bottom:4px;">Headline Options</div>
          <ol style="font-size:13px;color:#1a1a2e;margin:4px 0;padding-left:18px;">{headlines_html}</ol>
        </div>
        <div style="padding:12px 0;border-bottom:1px solid #eee;">
          <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#999;margin-bottom:4px;">Body Copy Draft</div>
          <div style="font-size:13px;color:#333;background:#f0f7ff;padding:12px 14px;border-radius:8px;line-height:1.6;">{body_draft}</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:12px 0;border-bottom:1px solid #eee;">
          <div>
            <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#999;margin-bottom:4px;">Tone</div>
            <div style="font-size:13px;color:#555;">{tone}</div>
          </div>
          <div>
            <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#999;margin-bottom:4px;">Format</div>
            <div style="font-size:13px;color:#555;">{fmt_rec}</div>
          </div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:12px 0;border-bottom:1px solid #eee;">
          <div>
            <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#999;margin-bottom:4px;">CTA</div>
            <div style="font-size:14px;font-weight:600;color:#1a73e8;">{cta}</div>
          </div>
          <div>
            <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#999;margin-bottom:4px;">Platform</div>
            <div style="font-size:13px;color:#555;text-transform:capitalize;">{platform}</div>
          </div>
        </div>
        <div style="padding:12px 0;border-bottom:1px solid #eee;">
          <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#999;margin-bottom:4px;">Visual Direction</div>
          <div style="font-size:13px;color:#555;">{visual}</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:12px 0;">
          <div style="background:#E8F5E9;padding:10px 14px;border-radius:8px;">
            <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#2E7D32;margin-bottom:4px;">What to Keep</div>
            <div style="font-size:13px;color:#333;">{what_keep}</div>
          </div>
          <div style="background:#FFF3E0;padding:10px 14px;border-radius:8px;">
            <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#E65100;margin-bottom:4px;">What to Change</div>
            <div style="font-size:13px;color:#333;">{what_change}</div>
          </div>
        </div>
      </div>
    </div>
"""
                    fill_gap_html += "  </div>\n</div>"
        except Exception as e:
            fill_gap_html = f"<!-- Fill-gap briefs unavailable: {e} -->"

        html += f"""
<div class="score-logic" id="gapMatrix" style="margin-top:24px;">
  <h3>Messaging Gap Matrix — Who's Saying What</h3>
  <p style="font-size:14px;color:var(--text-secondary);margin-bottom:16px;">
    Heatmap showing messaging angle coverage across advertisers. Red dots = Trilogy gaps. Darker = more ads.
  </p>
  {heatmap_svg}
  {gap_html}
  {fill_gap_html}
</div>
"""
    except Exception as e:
        html += f"<!-- Gap heatmap unavailable: {e} -->\n"

    # ── Volume Tracker ──
    try:
        from reports.volume_tracker import get_volume_tracker_html
        html += get_volume_tracker_html(cards)
    except Exception as e:
        html += f"<!-- Volume tracker unavailable: {e} -->\n"

    # ── Action Queue ──
    try:
        from reports.action_queue import get_action_queue_html
        html += get_action_queue_html()
    except Exception as e:
        html += f"<!-- Action queue unavailable: {e} -->\n"

    # ── Advertiser Sections ──
    for adv_name in advertiser_order:
        adv_ads = [c for c in cards if c["advertiser"] == adv_name]
        if not adv_ads:
            continue
        is_trilogy = adv_name == "Trilogy Care"
        adv_scores = [c["score"] for c in adv_ads if c["score"] >= 0]
        adv_avg = round(sum(adv_scores) / len(adv_scores), 1) if adv_scores else 0
        fb_count = sum(1 for c in adv_ads if c["source"] == "facebook")
        g_count = sum(1 for c in adv_ads if c["source"] == "google")

        html += f"""
<div class="advertiser-section" data-advertiser="{adv_name}" data-type="{'trilogy' if is_trilogy else 'competitor'}">
  <div class="advertiser-header">
    <h2>{adv_name}</h2>
    <span class="badge {'badge-trilogy' if is_trilogy else 'badge-competitor'}">{'Your Ads' if is_trilogy else 'Competitor'}</span>
    {"<span class='badge' style='background:#E8F5E9;color:var(--green)'>Avg: " + str(adv_avg) + "/100</span>" if adv_avg > 0 else ""}
    <span class="count">{len(adv_ads)} ads · {fb_count} Facebook · {g_count} Google</span>
  </div>
  <div class="ad-grid" id="grid-{adv_name.replace(' ','-')}">
"""
        for card_idx, card in enumerate(adv_ads):
            score = card["score"]
            sc = "var(--green)" if score >= 70 else "var(--yellow)" if score >= 50 else "var(--red)" if score >= 0 else "var(--text-tertiary)"
            has_img = bool(card["img"])
            fb_url = get_fb_embed_url(card) if card["source"] == "facebook" else card["ad_url"]

            freshness = card.get("freshness", "recent")
            freshness_badge = ""
            if freshness == "new":
                freshness_badge = '<span class="freshness-badge badge-new">NEW</span>'
            elif freshness == "stale":
                freshness_badge = '<span class="freshness-badge badge-stale">STALE</span>'

            # Gallery overlay
            g_score_bg = sc if score >= 0 else "var(--text-tertiary)"
            g_score_html = f'<span class="g-score" style="background:{g_score_bg}">{score}</span>' if score >= 0 else ""
            gallery_overlay = f'<div class="gallery-overlay"><span class="g-name">{card["advertiser"]}</span>{g_score_html}</div>'

            html += f"""    <div class="ad-card" data-platform="{card['source']}" data-format="{card['format']}" data-score="{score}" data-advertiser="{card['advertiser']}" data-freshness="{freshness}" data-idx="{card_idx}" data-date="{card.get('start_date', '')}">
      <div class="card-meta">
        <div class="platform">
          {'<svg width="18" height="18" viewBox="0 0 24 24" fill="#1877F2"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>' if card["source"] == "facebook" else '<svg width="18" height="18" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>'}
        </div>
        <div class="info">
          <div class="name">{card['advertiser']}</div>
          <div class="sub">{'Sponsored · ' if card['source'] == 'facebook' else ''}{card['start_date'] or card['source'].title()}</div>
        </div>
        {f'<span class="score-pill" style="background:{sc}">{score}</span>' if score >= 0 else ''}
        {freshness_badge}
      </div>
      <div class="card-creative" onclick="event.stopPropagation();openLightbox(this.closest('.ad-card'))">
        {f'<img src="{card["img"]}" alt="Ad creative" loading="lazy">' if has_img else '<div class="no-preview">No preview available · Click to view original</div>'}
        <span class="format-pill">{card['format'].upper()}</span>
        {f'<div class="play-btn"><svg width="24" height="24" viewBox="0 0 24 24" fill="white"><path d="M8 5v14l11-7z"/></svg></div>' if card['format'] == 'video' else ''}
        {f'<span class="versions">{card["versions"]} versions</span>' if card["versions"] > 1 else ''}
        {gallery_overlay}
      </div>
      <div class="card-copy">
        <p>{card["copy"][:250] if card["copy"] else "<em style=color:var(--text-tertiary)>No copy extracted</em>"}</p>
        <div class="tags">
          {f'<span class="tag tag-cta">{card["cta"]}</span>' if card["cta"] else ''}
          {f'<span class="tag tag-date">{card["start_date"]}</span>' if card["start_date"] else ''}
          {f'<span class="tag tag-id">ID: {card["library_id"]}</span>' if card["library_id"] else ''}
        </div>
      </div>
"""
            # Issues-first preview for cards scoring below 70
            issues = card.get("issues", [])
            if score >= 0 and score < 70 and issues:
                top_issue = issues[0].get("issue", "")[:80]
                html += f"""      <div class="card-issue-preview">
        <span class="issue-chip"><span class="issue-chip-dot"></span><span class="issue-chip-text">{top_issue}</span></span>
      </div>
"""

            html += """      <div class="card-detail">
"""
            # Score bars
            cats = card.get("cats", {})
            maxes = {"copy_quality": 25, "visual_quality": 20, "targeting_signals": 15,
                     "compliance": 15, "brand_consistency": 15, "freshness": 10}
            if cats:
                for ck, cd in cats.items():
                    if isinstance(cd, dict):
                        v = cd.get("score", 0)
                        mx = maxes.get(ck, 25)
                        pct = min(100, (v / mx) * 100) if mx > 0 else 0
                        cl = "var(--green)" if pct >= 70 else "var(--yellow)" if pct >= 50 else "var(--red)"
                        html += f'        <div class="score-row"><span class="lbl">{ck.replace("_"," ").title()[:10]}</span><div class="score-bar"><div class="score-bar-fill" style="width:{pct}%;background:{cl}"></div></div><span class="val">{v}</span></div>\n'

            # Issues
            issues = card.get("issues", [])
            if issues:
                html += '        <div class="issues-list">\n'
                for iss in issues[:3]:
                    sev = iss.get("severity", "low")
                    dc = "var(--red)" if sev == "critical" else "var(--orange)" if sev == "high" else "var(--yellow)" if sev == "medium" else "var(--text-tertiary)"
                    html += f'          <div class="issue-item"><span class="issue-dot" style="background:{dc}"></span>{iss.get("issue","")[:100]}</div>\n'
                html += '        </div>\n'

            review_key = card.get("library_id") or f"{card['source']}_{card['advertiser']}_{card.get('ad_index', 0)}"
            html += f"""      </div>
      <div class="card-footer">
        <button onclick="event.stopPropagation();toggleDetail(this.closest('.ad-card'))">Details</button>
        <button class="btn-primary" onclick="event.stopPropagation();window.open('{fb_url}','_blank')">View Original</button>
        <button class="save-to-board" onclick="event.stopPropagation();saveCardToBoard(this.closest('.ad-card'))" title="Save to Swipe File">☆</button>
        <div class="human-review" data-review-key="{review_key}">
          <button class="review-btn up-btn" onclick="event.stopPropagation();reviewAd('{review_key}','up')" title="Good ad">👍</button>
          <button class="review-btn down-btn" onclick="event.stopPropagation();reviewAd('{review_key}','down')" title="Poor ad">👎</button>
        </div>
      </div>
    </div>
"""
        html += "  </div>\n</div>\n"

    # ── Insights Drawer ──
    html += f"""
</div>

<div class="drawer-overlay" id="drawerOverlay" onclick="closeDrawer()"></div>
<div class="drawer" id="drawer">
  <button class="close-btn" onclick="closeDrawer()">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
  </button>
  <h2>Competitive Insights</h2>
  <p style="font-size:14px;color:var(--text-secondary);line-height:1.6;margin-bottom:16px;">{exec_summary}</p>

  <h3>Trilogy Strengths</h3>
  {"".join(f'<div class="insight-item" style="color:var(--green)">+ {s}</div>' for s in strengths)}

  <h3>Gaps vs Competitors</h3>
  {"".join(f'<div class="insight-item" style="color:var(--orange)">- {w}</div>' for w in weaknesses)}

  <h3>Recommendations</h3>
  {"".join(f'<div class="rec-item"><span class="rec-dot" style="background:{"var(--red)" if r.get("priority")=="high" else "var(--yellow)" if r.get("priority")=="medium" else "var(--accent)"}"></span><div><strong>{r.get("action","")}</strong><br><span style="font-size:12px;color:var(--text-tertiary)">{r.get("rationale","")}</span></div></div>' for r in recs)}
</div>

<script>
let currentTab = 'all';
let currentView = 'grid';
let filters = {{ platform: 'all', format: 'all', score: 'all', freshness: 'all' }};

function setTab(tab, btn) {{
  currentTab = tab;
  document.querySelectorAll('.header-nav button').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.advertiser-section').forEach(s => {{
    const type = s.dataset.type;
    if (tab === 'all') s.style.display = '';
    else if (tab === 'trilogy') s.style.display = type === 'trilogy' ? '' : 'none';
    else if (tab === 'competitors') s.style.display = type === 'competitor' ? '' : 'none';
  }});
}}

function toggleFilter(chip) {{
  const type = chip.dataset.filter;
  const val = chip.dataset.val;
  // Deactivate siblings of same filter type
  document.querySelectorAll(`.filter-chip[data-filter="${{type}}"]`).forEach(c => c.classList.remove('active'));
  if (filters[type] === val) {{
    filters[type] = 'all';
    document.querySelector(`.filter-chip[data-filter="${{type}}"][data-val="all"]`)?.classList.add('active');
  }} else {{
    filters[type] = val;
    chip.classList.add('active');
  }}
  filterAds();
}}

function filterAds() {{
  const q = document.querySelector('.search-input').value.toLowerCase();
  document.querySelectorAll('.ad-card').forEach(card => {{
    let show = true;
    if (filters.platform !== 'all' && card.dataset.platform !== filters.platform) show = false;
    if (filters.format !== 'all' && card.dataset.format !== filters.format) show = false;
    if (filters.score === 'poor' && parseInt(card.dataset.score) >= 50) show = false;
    if (filters.freshness !== 'all' && card.dataset.freshness !== filters.freshness) show = false;
    if (q && !card.innerText.toLowerCase().includes(q)) show = false;
    card.classList.toggle('hidden', !show);
  }});
}}

function sortAds(value) {{
  document.querySelectorAll('.ad-grid').forEach(grid => {{
    const cards = Array.from(grid.querySelectorAll('.ad-card'));
    if (value === 'default') {{
      // Restore original order via data-index
      cards.sort((a, b) => (parseInt(a.dataset.idx) || 0) - (parseInt(b.dataset.idx) || 0));
    }} else if (value === 'score_desc') {{
      cards.sort((a, b) => (parseInt(b.dataset.score) || 0) - (parseInt(a.dataset.score) || 0));
    }} else if (value === 'score_asc') {{
      cards.sort((a, b) => (parseInt(a.dataset.score) || 0) - (parseInt(b.dataset.score) || 0));
    }} else if (value === 'newest') {{
      cards.sort((a, b) => (b.dataset.date || '').localeCompare(a.dataset.date || ''));
    }} else if (value === 'oldest') {{
      cards.sort((a, b) => (a.dataset.date || '').localeCompare(b.dataset.date || ''));
    }}
    cards.forEach(c => grid.appendChild(c));
  }});
}}

function setView(mode, btn) {{
  currentView = mode;
  document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.ad-grid').forEach(g => {{
    g.classList.toggle('list-view', mode === 'list');
    g.classList.toggle('gallery-view', mode === 'gallery');
  }});
}}

function toggleDetail(card) {{
  card.classList.toggle('expanded');
}}

// Lazy load images using IntersectionObserver for performance
if ('IntersectionObserver' in window) {{
  const imgObserver = new IntersectionObserver((entries) => {{
    entries.forEach(entry => {{
      if (entry.isIntersecting) {{
        const img = entry.target;
        if (img.dataset.src) {{
          img.src = img.dataset.src;
          delete img.dataset.src;
        }}
        imgObserver.unobserve(img);
      }}
    }});
  }}, {{ rootMargin: '200px' }});
  document.querySelectorAll('.card-creative img[loading="lazy"]').forEach(img => imgObserver.observe(img));
}}

function openDrawer() {{
  document.getElementById('drawerOverlay').classList.add('open');
  document.getElementById('drawer').classList.add('open');
}}
function closeDrawer() {{
  document.getElementById('drawerOverlay').classList.remove('open');
  document.getElementById('drawer').classList.remove('open');
}}

function toggleScoreLogic() {{
  document.getElementById('scoreLogic').classList.toggle('visible');
  document.getElementById('marketVoice')?.classList.remove('visible');
}}
function toggleMarketVoice() {{
  document.getElementById('marketVoice')?.classList.toggle('visible');
  document.getElementById('scoreLogic')?.classList.remove('visible');
  document.getElementById('gapMatrix')?.classList.remove('visible');
}}
function toggleDarkMode() {{
  document.body.classList.toggle('dark-mode');
  const btn = document.getElementById('darkModeBtn');
  btn.textContent = document.body.classList.contains('dark-mode') ? '☀️' : '🌙';
  localStorage.setItem('tc_ads_dark', document.body.classList.contains('dark-mode'));
}}
// Auto-apply saved dark mode preference
if (localStorage.getItem('tc_ads_dark') === 'true') {{
  document.body.classList.add('dark-mode');
  document.getElementById('darkModeBtn').textContent = '☀️';
}}

function toggleExecView() {{
  document.getElementById('execView')?.classList.toggle('visible');
}}
function toggleActionQueue() {{
  const panels = ['scoreLogic','marketVoice','gapMatrix','volumeTracker','actionQueue','execView'];
  panels.forEach(id => {{
    const el = document.getElementById(id);
    if (el && id !== 'actionQueue') el.classList.remove('visible');
  }});
  document.getElementById('actionQueue')?.classList.toggle('visible');
}}
function toggleVolumeTracker() {{
  const panels = ['scoreLogic','marketVoice','gapMatrix','volumeTracker','execView'];
  panels.forEach(id => {{
    const el = document.getElementById(id);
    if (el && id !== 'volumeTracker') el.classList.remove('visible');
  }});
  document.getElementById('volumeTracker')?.classList.toggle('visible');
}}
function toggleGapMatrix() {{
  document.getElementById('gapMatrix')?.classList.toggle('visible');
  document.getElementById('scoreLogic')?.classList.remove('visible');
  document.getElementById('marketVoice')?.classList.remove('visible');
}}
</script>
"""

    # Inject compare + export addons
    try:
        from reports.dashboard_addons import get_compare_html, get_export_html, get_human_review_html, get_lightbox_html
        from reports.swipe_boards import get_swipe_boards_html
        html += get_compare_html()
        html += get_export_html({
            "total": len(cards),
            "trilogy": len(trilogy_cards),
            "avg_score": avg,
        })
        html += get_human_review_html()
        html += get_lightbox_html()
        html += get_swipe_boards_html()
        html += get_keyboard_shortcuts_html()
    except Exception as e:
        html += f"<!-- Addons failed: {{e}} -->"

    html += """
</body>
</html>"""

    path.write_text(html)
    print(f"  Dashboard v2 saved: {path}")
    return path
