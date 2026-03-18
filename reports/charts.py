"""
Inline SVG chart generators for the dashboard.
Market Voice Share treemap, Creative Mix bars, Quality Gap bars, Word Cloud.
"""
import math
import re
from collections import Counter


def market_voice_share_svg(messaging_data: dict, trilogy_share: dict, width: int = 800, height: int = 400) -> str:
    """
    Generate a treemap-style SVG showing market messaging share.
    messaging_data: {"empowerment_control": 34, "family_peace_of_mind": 18, ...}
    trilogy_share: {"empowerment_control": 60, ...} — Trilogy's % within each angle
    """
    if not messaging_data:
        return '<div style="padding:20px;color:#8A8D91;font-size:14px;">Messaging data not yet available. Run analysis with messaging taxonomy to generate this view.</div>'

    total = sum(messaging_data.values()) or 1
    sorted_angles = sorted(messaging_data.items(), key=lambda x: -x[1])

    # Color palette
    colors = [
        "#1877F2", "#31A24C", "#F7B928", "#E4405F", "#6366F1",
        "#06B6D4", "#F59E0B", "#EC4899", "#8B5CF6", "#14B8A6",
    ]

    angle_labels = {
        "empowerment_control": "Empowerment & Control",
        "family_peace_of_mind": "Family Peace of Mind",
        "cost_transparency": "Cost Transparency",
        "government_transition": "Govt Transition",
        "independence_dignity": "Independence & Dignity",
        "testimonial_social_proof": "Testimonials",
        "service_quality": "Service Quality",
        "convenience_speed": "Convenience & Speed",
        "self_managed": "Self-Managed",
        "community_belonging": "Community",
    }

    # Build horizontal stacked bar chart (more readable than treemap in HTML)
    bar_height = 48
    gap = 8
    label_width = 180
    bar_area = width - label_width - 80
    chart_height = (bar_height + gap) * len(sorted_angles) + 40

    svg = f'<svg width="{width}" height="{chart_height}" viewBox="0 0 {width} {chart_height}" xmlns="http://www.w3.org/2000/svg">\n'
    svg += '<style>text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }</style>\n'

    y = 20
    for i, (angle, count) in enumerate(sorted_angles):
        pct = (count / total) * 100
        bar_w = (count / total) * bar_area
        label = angle_labels.get(angle, angle.replace("_", " ").title())
        color = colors[i % len(colors)]
        t_share = trilogy_share.get(angle, 0)
        t_bar_w = (t_share / 100) * bar_w if bar_w > 0 else 0

        # Background bar (total market)
        svg += f'  <rect x="{label_width}" y="{y}" width="{bar_w}" height="{bar_height}" rx="6" fill="{color}" opacity="0.25"/>\n'
        # Trilogy's share within
        if t_bar_w > 2:
            svg += f'  <rect x="{label_width}" y="{y}" width="{t_bar_w}" height="{bar_height}" rx="6" fill="{color}"/>\n'
        # Label
        svg += f'  <text x="{label_width - 8}" y="{y + bar_height/2 + 5}" text-anchor="end" font-size="13" font-weight="500" fill="#1C1E21">{label}</text>\n'
        # Percentage
        svg += f'  <text x="{label_width + bar_w + 8}" y="{y + bar_height/2 + 5}" font-size="12" font-weight="600" fill="#606770">{pct:.0f}%</text>\n'
        # Trilogy share label inside bar
        if t_bar_w > 40:
            svg += f'  <text x="{label_width + t_bar_w/2}" y="{y + bar_height/2 + 5}" text-anchor="middle" font-size="11" font-weight="600" fill="white">TC {t_share:.0f}%</text>\n'

        y += bar_height + gap

    # Legend
    svg += f'  <rect x="{label_width}" y="{y + 5}" width="16" height="16" rx="3" fill="#1877F2"/>\n'
    svg += f'  <text x="{label_width + 22}" y="{y + 17}" font-size="12" fill="#606770">Trilogy Care share</text>\n'
    svg += f'  <rect x="{label_width + 160}" y="{y + 5}" width="16" height="16" rx="3" fill="#1877F2" opacity="0.25"/>\n'
    svg += f'  <text x="{label_width + 182}" y="{y + 17}" font-size="12" fill="#606770">Total market</text>\n'

    svg += '</svg>'
    return svg


def creative_mix_svg(data: dict, width: int = 600, height: int = 300) -> str:
    """
    Stacked bar chart showing video/image/text split per advertiser.
    data: {"Trilogy Care": {"video": 8, "image": 15, "text": 7}, ...}
    """
    if not data:
        return ""

    bar_height = 28
    gap = 6
    label_width = 140
    bar_area = width - label_width - 20
    chart_height = (bar_height + gap) * len(data) + 20

    colors = {"video": "#E4405F", "image": "#1877F2", "text": "#31A24C"}

    svg = f'<svg width="{width}" height="{chart_height}" viewBox="0 0 {width} {chart_height}" xmlns="http://www.w3.org/2000/svg">\n'
    svg += '<style>text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }</style>\n'

    y = 10
    for name, formats in sorted(data.items()):
        total = sum(formats.values()) or 1
        x = label_width

        svg += f'  <text x="{label_width - 8}" y="{y + bar_height/2 + 4}" text-anchor="end" font-size="12" font-weight="500" fill="#1C1E21">{name[:16]}</text>\n'

        for fmt in ["video", "image", "text"]:
            count = formats.get(fmt, 0)
            w = (count / total) * bar_area
            if w > 0:
                svg += f'  <rect x="{x}" y="{y}" width="{w}" height="{bar_height}" fill="{colors[fmt]}"/>\n'
                if w > 25:
                    svg += f'  <text x="{x + w/2}" y="{y + bar_height/2 + 4}" text-anchor="middle" font-size="10" font-weight="600" fill="white">{count}</text>\n'
                x += w

        y += bar_height + gap

    # Legend
    for i, (fmt, color) in enumerate(colors.items()):
        lx = label_width + i * 80
        svg += f'  <rect x="{lx}" y="{y + 2}" width="12" height="12" rx="2" fill="{color}"/>\n'
        svg += f'  <text x="{lx + 16}" y="{y + 12}" font-size="11" fill="#606770">{fmt.title()}</text>\n'

    svg += '</svg>'
    return svg


def quality_gap_svg(data: dict, width: int = 600, height: int = 300) -> str:
    """
    Horizontal bar chart showing quality score comparison.
    data: {"Trilogy Care": 82, "Bolton Clarke": 68, ...}
    """
    if not data:
        return ""

    trilogy_score = data.get("Trilogy Care", 0)
    bar_height = 32
    gap = 8
    label_width = 140
    bar_area = width - label_width - 60
    sorted_data = sorted(data.items(), key=lambda x: -x[1])
    chart_height = (bar_height + gap) * len(sorted_data) + 10

    svg = f'<svg width="{width}" height="{chart_height}" viewBox="0 0 {width} {chart_height}" xmlns="http://www.w3.org/2000/svg">\n'
    svg += '<style>text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }</style>\n'

    y = 5
    for name, score in sorted_data:
        bar_w = (score / 100) * bar_area
        is_trilogy = name == "Trilogy Care"
        color = "#1877F2" if is_trilogy else ("#31A24C" if score >= trilogy_score else "#E4405F" if score < trilogy_score - 10 else "#F7B928")

        svg += f'  <rect x="{label_width}" y="{y}" width="{bar_w}" height="{bar_height}" rx="4" fill="{color}" opacity="{"1" if is_trilogy else "0.7"}"/>\n'
        svg += f'  <text x="{label_width - 8}" y="{y + bar_height/2 + 4}" text-anchor="end" font-size="12" font-weight="{"700" if is_trilogy else "500"}" fill="#1C1E21">{name[:16]}</text>\n'
        svg += f'  <text x="{label_width + bar_w + 6}" y="{y + bar_height/2 + 4}" font-size="12" font-weight="700" fill="{color}">{score}</text>\n'

        y += bar_height + gap

    svg += '</svg>'
    return svg


def messaging_gap_heatmap_svg(matrix: dict, width: int = 900, height: int = 500) -> str:
    """
    Heatmap SVG showing messaging angle coverage across advertisers.
    matrix: {"matrix": {"empowerment_control": {"Trilogy Care": 5, "Bolton Clarke": 2, ...}, ...}}
    Rows = messaging angles, Columns = advertisers (Trilogy Care first, rest sorted).
    Color intensity encodes ad count; gap cells (Trilogy=0, others>0) get a red warning dot.
    """
    raw = matrix.get("matrix", {})
    if not raw:
        return '<div style="padding:20px;color:#8A8D91;font-size:14px;">Messaging matrix not yet available.</div>'

    angle_labels = {
        "empowerment_control": "Empowerment & Control",
        "family_peace_of_mind": "Family Peace of Mind",
        "cost_transparency": "Cost Transparency",
        "government_transition": "Govt Transition",
        "independence_dignity": "Independence & Dignity",
        "testimonial_social_proof": "Testimonials",
        "service_quality": "Service Quality",
        "convenience_speed": "Convenience & Speed",
        "self_managed": "Self-Managed",
        "community_belonging": "Community",
    }

    # Collect all advertisers across every angle
    all_advertisers: set[str] = set()
    for counts in raw.values():
        all_advertisers.update(counts.keys())

    # Trilogy Care first, then the rest alphabetically
    advertisers: list[str] = []
    if "Trilogy Care" in all_advertisers:
        advertisers.append("Trilogy Care")
        all_advertisers.discard("Trilogy Care")
    advertisers.extend(sorted(all_advertisers))

    angles = list(raw.keys())

    # Layout constants
    row_label_width = 180
    header_height = 120  # room for rotated column headers
    cell_w = max(56, min(80, (width - row_label_width - 20) // max(len(advertisers), 1)))
    cell_h = 34
    chart_width = row_label_width + cell_w * len(advertisers) + 20
    chart_height = header_height + cell_h * len(angles) + 40

    # Colors
    bg = "#FFFFFF"
    empty = "#F0F2F5"
    low = "#DBEAFE"       # 1-2
    mid = "#93C5FD"       # 3-5
    high = "#3B82F6"      # 6+
    gap_bg = "#FEE2E2"
    whitespace_bg = "#ECFDF5"
    text_color = "#1C1E21"
    muted = "#8A8D91"

    def cell_color(count: int, is_gap: bool, is_whitespace: bool) -> str:
        if is_gap:
            return gap_bg
        if is_whitespace:
            return whitespace_bg
        if count == 0:
            return empty
        if count <= 2:
            return low
        if count <= 5:
            return mid
        return high

    svg = f'<svg width="{chart_width}" height="{chart_height}" viewBox="0 0 {chart_width} {chart_height}" xmlns="http://www.w3.org/2000/svg">\n'
    svg += f'<rect width="{chart_width}" height="{chart_height}" fill="{bg}"/>\n'
    svg += '<style>text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }</style>\n'

    # Column headers (rotated 45 degrees)
    for ci, adv in enumerate(advertisers):
        cx = row_label_width + ci * cell_w + cell_w / 2
        cy = header_height - 8
        svg += f'  <text x="{cx}" y="{cy}" font-size="11" font-weight="{"700" if adv == "Trilogy Care" else "500"}" fill="{text_color}" text-anchor="start" transform="rotate(-45,{cx},{cy})">{adv}</text>\n'

    # Trilogy Care column accent border (gold left edge)
    if advertisers and advertisers[0] == "Trilogy Care":
        tc_x = row_label_width
        svg += f'  <rect x="{tc_x}" y="{header_height}" width="3" height="{cell_h * len(angles)}" fill="#F59E0B"/>\n'

    # Grid rows
    for ri, angle in enumerate(angles):
        y = header_height + ri * cell_h
        label = angle_labels.get(angle, angle.replace("_", " ").title())
        counts = raw.get(angle, {})

        # Row label
        svg += f'  <text x="{row_label_width - 10}" y="{y + cell_h / 2 + 4}" text-anchor="end" font-size="12" font-weight="500" fill="{text_color}">{label}</text>\n'

        # Check if anyone uses this angle
        any_nonzero = any(counts.get(a, 0) > 0 for a in advertisers)
        tc_count = counts.get("Trilogy Care", 0)

        for ci, adv in enumerate(advertisers):
            x = row_label_width + ci * cell_w
            count = counts.get(adv, 0)

            # Determine cell state
            is_gap = (adv == "Trilogy Care" and tc_count == 0
                      and any(counts.get(a, 0) > 0 for a in advertisers if a != "Trilogy Care"))
            is_whitespace = (not any_nonzero)

            fill = cell_color(count, is_gap, is_whitespace)

            # Cell rect with thin border
            svg += f'  <rect x="{x + 1}" y="{y + 1}" width="{cell_w - 2}" height="{cell_h - 2}" rx="3" fill="{fill}" stroke="#E4E6EB" stroke-width="0.5"/>\n'

            # Count number
            font_color = "white" if count >= 6 else text_color
            if count > 0:
                svg += f'  <text x="{x + cell_w / 2}" y="{y + cell_h / 2 + 4}" text-anchor="middle" font-size="12" font-weight="600" fill="{font_color}">{count}</text>\n'

            # Gap warning: red dot in top-right corner
            if is_gap:
                dot_x = x + cell_w - 10
                dot_y = y + 10
                svg += f'  <circle cx="{dot_x}" cy="{dot_y}" r="4" fill="#EF4444"/>\n'

    # Legend
    ly = header_height + cell_h * len(angles) + 16
    items = [
        (empty, "0 ads"), (low, "1-2"), (mid, "3-5"), (high, "6+"),
        (gap_bg, "Gap (TC=0)"), (whitespace_bg, "Whitespace"),
    ]
    lx = row_label_width
    for color, label in items:
        svg += f'  <rect x="{lx}" y="{ly}" width="14" height="14" rx="3" fill="{color}" stroke="#E4E6EB" stroke-width="0.5"/>\n'
        svg += f'  <text x="{lx + 18}" y="{ly + 11}" font-size="11" fill="{muted}">{label}</text>\n'
        lx += 90

    svg += '</svg>'
    return svg


def word_cloud_svg(ads: list[dict], width: int = 700, height: int = 300) -> str:
    """
    Generate a word cloud as inline SVG from ad copy text.
    Extracts words from copy_text/full_text fields, counts frequencies,
    and renders top 30 words sized proportionally.
    """
    STOP_WORDS = {
        "the", "a", "an", "is", "are", "to", "for", "of", "in", "and",
        "with", "your", "you", "our", "we", "that", "this", "from", "or",
        "by", "on", "at", "it", "be", "as", "but", "not", "has", "have",
        "been", "was", "were", "their", "can", "more", "will", "do", "if",
        "about", "all", "so", "up", "no", "get", "than", "into", "just",
        "over", "also", "how", "its",
    }

    # Extract all text
    all_text = []
    for ad in ads:
        text = (ad.get("copy_text", "") or "") + " " + (ad.get("full_text", "") or "")
        all_text.append(text)

    combined = " ".join(all_text).lower()
    # Keep only letters and spaces
    combined = re.sub(r"[^a-z\s]", " ", combined)
    words = [w for w in combined.split() if len(w) > 2 and w not in STOP_WORDS]

    if not words:
        return '<div style="padding:20px;color:#8A8D91;font-size:14px;">No ad copy text available for word cloud.</div>'

    freq = Counter(words).most_common(30)
    if not freq:
        return '<div style="padding:20px;color:#8A8D91;font-size:14px;">No words to display.</div>'

    max_count = freq[0][1]
    min_count = freq[-1][1]
    count_range = max(max_count - min_count, 1)

    # Blue palette
    colors = ["#1877F2", "#1565C0", "#1E88E5", "#2196F3", "#42A5F5",
              "#64B5F6", "#0D47A1", "#1976D2", "#2962FF", "#448AFF"]

    min_font = 12
    max_font = 40

    svg = f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">\n'
    svg += '<style>text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }</style>\n'

    # Simple row-based layout
    padding_x = 16
    padding_y = 16
    x = padding_x
    y = padding_y
    line_height = 0

    for i, (word, count) in enumerate(freq):
        # Scale font size proportionally
        t = (count - min_count) / count_range
        font_size = min_font + t * (max_font - min_font)
        font_weight = "700" if t > 0.5 else "600" if t > 0.2 else "500"
        color = colors[i % len(colors)]

        # Estimate word width (rough: 0.6 * font_size per character)
        word_width = len(word) * font_size * 0.6 + 12

        # Wrap to next line if needed
        if x + word_width > width - padding_x:
            x = padding_x
            y += line_height + 8
            line_height = 0

        if y + font_size > height - padding_y:
            break  # Out of space

        line_height = max(line_height, font_size + 4)
        opacity = 0.7 + 0.3 * t

        svg += f'  <text x="{x}" y="{y + font_size}" font-size="{font_size:.0f}" font-weight="{font_weight}" fill="{color}" opacity="{opacity:.2f}">{word}</text>\n'
        x += word_width

    svg += '</svg>'
    return svg
