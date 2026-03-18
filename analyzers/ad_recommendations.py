"""
Ad Recommendations Engine — analyzes Trilogy's ads and recommends actions.
Turn off low performers, double down on high performers, fill messaging gaps.
"""
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def generate_recommendations(
    trilogy_ads: list[dict],
    trilogy_results: list[dict],
    messaging_gaps: dict = None,
) -> dict:
    """
    Generate actionable recommendations for Trilogy Care's ad portfolio.
    """
    recs = {
        "turn_off": [],
        "optimize": [],
        "keep_running": [],
        "new_ads_needed": [],
        "summary": "",
    }

    # Match results to ads
    scored = []
    for i, ad in enumerate(trilogy_ads):
        # Find matching analysis
        analysis = None
        if i < len(trilogy_results):
            analysis = trilogy_results[i]
        elif len(trilogy_results) > 0:
            # Try to find by index
            for r in trilogy_results:
                src = r.get("source_ad", {})
                if src.get("ad_index") == ad.get("ad_index"):
                    analysis = r
                    break

        score = analysis.get("overall_score", -1) if analysis else -1
        issues = analysis.get("issues", []) if analysis else []
        angles = analysis.get("messaging_angles", []) if analysis else []
        concept = analysis.get("campaign_concept", "") if analysis else ""

        scored.append({
            "ad": ad,
            "score": score,
            "issues": issues,
            "angles": angles,
            "concept": concept,
            "library_id": ad.get("library_id", ""),
            "copy_preview": (ad.get("copy_text") or ad.get("full_text", ""))[:100],
        })

    # Sort by score
    scored.sort(key=lambda x: x["score"])

    # Turn off: score < 40 with critical/high issues
    for s in scored:
        if s["score"] < 40 and s["score"] >= 0:
            critical = [i for i in s["issues"] if i.get("severity") in ("critical", "high")]
            if critical:
                recs["turn_off"].append({
                    "library_id": s["library_id"],
                    "score": s["score"],
                    "reason": critical[0].get("issue", "Low quality"),
                    "copy_preview": s["copy_preview"],
                })

    # Optimize: score 40-69 — worth fixing, not worth killing
    for s in scored:
        if 40 <= s["score"] < 70:
            top_issue = s["issues"][0] if s["issues"] else {}
            recs["optimize"].append({
                "library_id": s["library_id"],
                "score": s["score"],
                "fix": top_issue.get("recommendation", "Review and optimize"),
                "copy_preview": s["copy_preview"],
            })

    # Keep running: score >= 70
    for s in scored:
        if s["score"] >= 70:
            recs["keep_running"].append({
                "library_id": s["library_id"],
                "score": s["score"],
                "concept": s["concept"],
                "copy_preview": s["copy_preview"],
            })

    # New ads needed: from messaging gaps
    if messaging_gaps:
        gaps = messaging_gaps.get("gaps", {}).get("gaps", [])
        for g in gaps[:3]:
            recs["new_ads_needed"].append({
                "angle": g["angle"],
                "competitor_count": g["competitor_count"],
                "rationale": f"{g['competitor_count']} competitors use this messaging, Trilogy has 0 ads",
            })

    # Also check for under-represented angles from Trilogy's own data
    angle_counts = {}
    for s in scored:
        for a in s["angles"]:
            angle_counts[a] = angle_counts.get(a, 0) + 1
    all_angles = ["empowerment_control", "family_peace_of_mind", "cost_transparency",
                  "government_transition", "independence_dignity", "testimonial_social_proof",
                  "service_quality", "convenience_speed", "self_managed", "community_belonging"]
    for angle in all_angles:
        if angle not in angle_counts:
            recs["new_ads_needed"].append({
                "angle": angle,
                "competitor_count": 0,
                "rationale": f"Trilogy has 0 ads using '{angle.replace('_', ' ')}' messaging",
            })

    # Summary
    recs["summary"] = (
        f"Portfolio: {len(scored)} ads. "
        f"Turn off: {len(recs['turn_off'])}. "
        f"Optimize: {len(recs['optimize'])}. "
        f"Keep: {len(recs['keep_running'])}. "
        f"Gaps to fill: {len(recs['new_ads_needed'])}."
    )

    return recs
