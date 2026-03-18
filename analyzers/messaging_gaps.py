"""
Messaging Gap Analyzer — builds a matrix of messaging angles by advertiser
and identifies gaps where Trilogy Care is absent but competitors are active.
"""

import re
from collections import defaultdict

# Keyword patterns for estimating messaging angles from ad copy
ANGLE_KEYWORDS: dict[str, list[str]] = {
    "empowerment_control": [
        "choose", "control", "your choice", "self-managed", "driver's seat",
    ],
    "family_peace_of_mind": [
        "family", "peace of mind", "loved ones", "children", "daughter", "son",
    ],
    "cost_transparency": [
        "fee", "cost", "transparent", "no hidden", "pricing", "affordable",
        "26%", "low rate",
    ],
    "government_transition": [
        "support at home program", "government", "new program", "transition",
        "classification",
    ],
    "independence_dignity": [
        "independence", "dignity", "independent", "home you love", "stay at home",
    ],
    "testimonial_social_proof": [
        "testimonial", "review", "story", "experience", "peter", "client",
    ],
    "service_quality": [
        "quality", "professional", "qualified", "experienced", "registered",
    ],
    "convenience_speed": [
        "fast", "quick", "same day", "today", "easy", "simple",
    ],
    "self_managed": [
        "self-managed", "self managed", "manage your own", "your way",
    ],
    "community_belonging": [
        "community", "social", "connected", "belong", "friends",
    ],
}

# Advertisers considered "Trilogy Care"
_TRILOGY_NAMES = {"trilogycare", "trilogy care", "trilogy"}


def _normalise_advertiser(name: str) -> str:
    """Return a canonical advertiser name."""
    return (name or "Unknown").strip()


def _is_trilogy(advertiser: str) -> bool:
    return advertiser.lower().strip() in _TRILOGY_NAMES


def _get_ad_text(ad: dict) -> str:
    """Combine all available text fields from a raw ad."""
    parts = []
    for key in ("copy_text", "full_text", "body", "description", "headline"):
        val = ad.get(key)
        if val:
            parts.append(str(val))
    return " ".join(parts)


# ── Public API ──────────────────────────────────────────────────────────────


def estimate_messaging_angles(ad_text: str) -> list[str]:
    """Estimate messaging angles from ad copy using keyword matching.

    Returns a list of matched angle keys.
    """
    text_lower = ad_text.lower()
    matched: list[str] = []
    for angle, keywords in ANGLE_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                matched.append(angle)
                break
    return matched


def build_messaging_matrix(
    all_ads: list[dict],
    analysis_results: list[dict],
) -> dict:
    """Build a matrix of {angle: {advertiser: count}} from ads + analysis.

    Parameters
    ----------
    all_ads : list[dict]
        Raw ad dicts (must contain 'advertiser' and text fields).
    analysis_results : list[dict]
        Quality-analyzer output dicts; may contain 'messaging_angles' and
        'source_ad' with an 'advertiser' key.

    Returns
    -------
    dict with keys:
        matrix     — {angle: {advertiser: count}}
        ad_angles  — [{advertiser, angles, text_snippet, source}] per ad
        totals     — {advertiser: total_ads_with_angles}
    """

    # Index analysis results by a composite key so we can match them to raw ads
    result_index: dict[str, dict] = {}
    for res in analysis_results:
        src = res.get("source_ad", {})
        lid = src.get("library_id", "")
        adv = src.get("advertiser", "")
        idx = src.get("ad_index", "")
        key = lid if lid else f"{src.get('source', '')}_{adv}_{idx}"
        result_index[key] = res

    matrix: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    ad_angles_list: list[dict] = []
    totals: dict[str, int] = defaultdict(int)

    for ad in all_ads:
        advertiser = _normalise_advertiser(ad.get("advertiser", ""))
        lid = ad.get("library_id", "")
        key = lid if lid else (
            f"{ad.get('source', '')}_{ad.get('advertiser', '')}_{ad.get('ad_index', '')}"
        )

        # Try to pull messaging_angles from the analysis result first
        result = result_index.get(key, {})
        angles = result.get("messaging_angles")

        if not angles:
            # Fall back to keyword estimation
            text = _get_ad_text(ad)
            angles = estimate_messaging_angles(text)

        if not angles:
            continue

        totals[advertiser] += 1

        snippet = (_get_ad_text(ad) or "")[:120]

        for angle in angles:
            matrix[angle][advertiser] += 1

        ad_angles_list.append({
            "advertiser": advertiser,
            "angles": angles,
            "text_snippet": snippet,
            "source": "analysis" if result.get("messaging_angles") else "estimated",
        })

    return {
        "matrix": {a: dict(advs) for a, advs in matrix.items()},
        "ad_angles": ad_angles_list,
        "totals": dict(totals),
    }


def find_gaps(matrix_result: dict) -> dict:
    """Identify messaging gaps, whitespace, and crowded angles.

    Parameters
    ----------
    matrix_result : dict
        Output of build_messaging_matrix().

    Returns
    -------
    dict with keys:
        gaps        — angles where Trilogy has 0 ads but competitors have > 0
        whitespace  — angles where NO advertiser has ads (potential opportunity)
        crowded     — angles where 3+ advertisers are active
        inspiration — {angle: [competitor ad snippets]}
        trilogy_angles — angles Trilogy IS using
    """

    matrix = matrix_result.get("matrix", {})
    ad_angles_list = matrix_result.get("ad_angles", [])

    # Collect all advertisers
    all_advertisers: set[str] = set()
    for advs in matrix.values():
        all_advertisers.update(advs.keys())

    trilogy_advertisers = {a for a in all_advertisers if _is_trilogy(a)}
    competitor_advertisers = all_advertisers - trilogy_advertisers

    all_angles = set(ANGLE_KEYWORDS.keys())
    active_angles = set(matrix.keys())

    gaps: list[dict] = []
    crowded: list[dict] = []
    trilogy_angles: list[str] = []

    for angle in sorted(all_angles):
        advs = matrix.get(angle, {})
        trilogy_count = sum(advs.get(t, 0) for t in trilogy_advertisers)
        comp_counts = {a: advs.get(a, 0) for a in competitor_advertisers if advs.get(a, 0) > 0}
        total_comp = sum(comp_counts.values())

        if trilogy_count > 0:
            trilogy_angles.append(angle)

        if trilogy_count == 0 and total_comp > 0:
            gaps.append({
                "angle": angle,
                "competitor_count": total_comp,
                "competitors": comp_counts,
            })

        num_active = len(comp_counts) + (1 if trilogy_count > 0 else 0)
        if num_active >= 3:
            crowded.append({
                "angle": angle,
                "active_advertisers": num_active,
                "total_ads": trilogy_count + total_comp,
            })

    # Whitespace — angles in taxonomy that nobody is using
    whitespace = [
        {"angle": a} for a in sorted(all_angles - active_angles)
    ]

    # Inspiration — for each gap, pull competitor ad snippets
    inspiration: dict[str, list[str]] = {}
    for gap in gaps:
        angle = gap["angle"]
        snippets: list[str] = []
        for entry in ad_angles_list:
            if angle in entry["angles"] and not _is_trilogy(entry["advertiser"]):
                snippet = f"[{entry['advertiser']}] {entry['text_snippet']}"
                if snippet not in snippets:
                    snippets.append(snippet)
                if len(snippets) >= 5:
                    break
        inspiration[angle] = snippets

    return {
        "gaps": gaps,
        "whitespace": whitespace,
        "crowded": crowded,
        "inspiration": inspiration,
        "trilogy_angles": trilogy_angles,
    }
