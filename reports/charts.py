"""
Inline SVG chart generators for the dashboard.
Market Voice Share treemap, Creative Mix bars, Quality Gap bars.
"""


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
