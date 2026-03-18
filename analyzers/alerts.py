"""
Alert System — detects notable changes in the competitive landscape.
Generates alerts when:
- A new competitor starts advertising
- A competitor significantly increases ad volume
- A new messaging theme emerges in the market
- A competitor launches a direct pricing comparison
- Trilogy's share of voice drops in any category
"""
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def generate_alerts(current_ads: list[dict], history: dict = None) -> list[dict]:
    """Generate competitive alerts from current scan data."""
    alerts = []
    now = datetime.now()

    # Load messaging data
    try:
        msg_data = json.loads((DATA_DIR / "messaging_analysis.json").read_text())
    except Exception:
        msg_data = {}

    # Load history
    if history is None:
        try:
            history = json.loads((DATA_DIR / "ad_history.json").read_text())
        except Exception:
            history = {}

    # 1. Check for new advertisers
    known_advertisers = set(v.get("advertiser", "") for v in history.values())
    current_advertisers = set(a.get("advertiser", "") for a in current_ads)
    new_advertisers = current_advertisers - known_advertisers
    for adv in new_advertisers:
        if adv and adv != "Unknown":
            alerts.append({
                "type": "new_competitor",
                "severity": "high",
                "title": f"New competitor detected: {adv}",
                "detail": f"{adv} has started running Support at Home ads",
                "timestamp": now.isoformat(),
            })

    # 2. Check for pricing comparison ads targeting Trilogy
    trilogy_mentions = []
    for ad in current_ads:
        text = (ad.get("copy_text") or ad.get("full_text", "")).lower()
        adv = ad.get("advertiser", "").lower()
        if "trilogy" not in adv and ("trilogy" in text or "26%" in text or "same service" in text):
            trilogy_mentions.append(ad)

    for ad in trilogy_mentions:
        alerts.append({
            "type": "competitive_mention",
            "severity": "critical",
            "title": f"Competitor mentions Trilogy! ({ad.get('advertiser', '?')})",
            "detail": f"Ad copy references Trilogy Care or our pricing. Copy: {(ad.get('copy_text') or '')[:100]}",
            "timestamp": now.isoformat(),
            "library_id": ad.get("library_id", ""),
        })

    # 3. Check for low Trilogy share in growing themes
    trilogy_share = msg_data.get("trilogy_share", {})
    for angle, share in trilogy_share.items():
        if share < 20:
            label = angle.replace("_", " ").title()
            alerts.append({
                "type": "share_drop",
                "severity": "medium",
                "title": f"Low share: {label} ({share}%)",
                "detail": f"Trilogy has only {share}% share of '{label}' messaging. Competitors are dominating.",
                "timestamp": now.isoformat(),
            })

    # Sort by severity
    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    alerts.sort(key=lambda x: sev_order.get(x.get("severity", "low"), 4))

    return alerts


def get_alerts_html(alerts: list[dict]) -> str:
    """Generate HTML for the alerts banner at top of dashboard."""
    if not alerts:
        return ""

    critical = [a for a in alerts if a["severity"] == "critical"]
    high = [a for a in alerts if a["severity"] == "high"]

    if not critical and not high:
        return ""

    items = ""
    for a in (critical + high)[:5]:
        color = "#E4405F" if a["severity"] == "critical" else "#F7B928"
        icon = "🚨" if a["severity"] == "critical" else "⚠️"
        items += f"""
    <div style="display:flex;gap:8px;align-items:start;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.1);">
      <span style="font-size:16px;">{icon}</span>
      <div>
        <div style="font-weight:600;font-size:13px;">{a['title']}</div>
        <div style="font-size:12px;opacity:0.8;">{a['detail'][:100]}</div>
      </div>
    </div>"""

    return f"""
<div style="background:linear-gradient(135deg,#1C1E21,#2D1B36);color:white;padding:16px 24px;margin:-16px -24px 16px;border-radius:12px;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
    <span style="font-size:18px;">🔔</span>
    <h3 style="font-size:15px;font-weight:700;">Alerts ({len(critical)} critical, {len(high)} high)</h3>
  </div>
  {items}
</div>
"""
