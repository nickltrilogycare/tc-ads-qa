"""
Ad Volume Tracker — generates a competitive volume comparison table.
Shows who's running the most ads, format split, and intensity signals.
"""


def get_volume_tracker_html(cards: list[dict]) -> str:
    """Generate an ad volume comparison table sorted by ad count."""
    from collections import defaultdict

    # Aggregate by advertiser
    by_adv = defaultdict(lambda: {"total": 0, "video": 0, "image": 0, "text": 0, "fb": 0, "google": 0, "scores": []})

    for c in cards:
        adv = c.get("advertiser", "Unknown")
        by_adv[adv]["total"] += 1
        fmt = c.get("format", "image")
        if fmt in by_adv[adv]:
            by_adv[adv][fmt] += 1
        if c.get("source") == "facebook":
            by_adv[adv]["fb"] += 1
        else:
            by_adv[adv]["google"] += 1
        if c.get("score", -1) >= 0:
            by_adv[adv]["scores"].append(c["score"])

    # Sort by total ads
    sorted_advs = sorted(by_adv.items(), key=lambda x: -x[1]["total"])

    rows = ""
    for rank, (adv, data) in enumerate(sorted_advs, 1):
        avg = round(sum(data["scores"]) / len(data["scores"]), 1) if data["scores"] else "—"
        is_trilogy = adv == "Trilogy Care"
        row_style = "background:#EBF5FF;font-weight:600;" if is_trilogy else ""
        score_color = "#31A24C" if isinstance(avg, (int, float)) and avg >= 70 else "#F7B928" if isinstance(avg, (int, float)) and avg >= 50 else "#E4405F" if isinstance(avg, (int, float)) else "#8A8D91"

        # Volume bar
        max_total = sorted_advs[0][1]["total"] if sorted_advs else 1
        bar_pct = (data["total"] / max_total) * 100

        rows += f"""<tr style="{row_style}">
  <td style="width:30px;color:#8A8D91;font-size:12px;">{rank}</td>
  <td style="font-weight:{'700' if is_trilogy else '500'};">{adv}</td>
  <td style="font-weight:700;">{data['total']}</td>
  <td><div style="background:#E4E6EB;border-radius:3px;height:8px;width:100%;"><div style="background:{'#1877F2' if is_trilogy else '#93C5FD'};height:8px;border-radius:3px;width:{bar_pct}%;"></div></div></td>
  <td style="color:#E4405F;">{data['video']}</td>
  <td style="color:#1877F2;">{data['image']}</td>
  <td>{data['text']}</td>
  <td>{data['fb']}</td>
  <td>{data['google']}</td>
  <td style="color:{score_color};font-weight:600;">{avg}</td>
</tr>"""

    return f"""
<div class="score-logic" id="volumeTracker" style="margin-top:24px;">
  <h3>Competitive Ad Volume</h3>
  <p style="font-size:14px;color:var(--text-secondary);margin-bottom:16px;">
    Who's running the most Support at Home ads? Sorted by total active ad count.
  </p>
  <table style="width:100%;border-collapse:collapse;font-size:13px;">
    <thead>
      <tr style="border-bottom:2px solid var(--border);">
        <th style="padding:8px;text-align:left;color:var(--text-tertiary);font-size:11px;">#</th>
        <th style="padding:8px;text-align:left;color:var(--text-tertiary);font-size:11px;">ADVERTISER</th>
        <th style="padding:8px;text-align:left;color:var(--text-tertiary);font-size:11px;">ADS</th>
        <th style="padding:8px;text-align:left;color:var(--text-tertiary);font-size:11px;width:120px;">VOLUME</th>
        <th style="padding:8px;text-align:left;color:var(--text-tertiary);font-size:11px;">VID</th>
        <th style="padding:8px;text-align:left;color:var(--text-tertiary);font-size:11px;">IMG</th>
        <th style="padding:8px;text-align:left;color:var(--text-tertiary);font-size:11px;">TXT</th>
        <th style="padding:8px;text-align:left;color:var(--text-tertiary);font-size:11px;">FB</th>
        <th style="padding:8px;text-align:left;color:var(--text-tertiary);font-size:11px;">GOOG</th>
        <th style="padding:8px;text-align:left;color:var(--text-tertiary);font-size:11px;">AVG SCORE</th>
      </tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>
</div>
"""
