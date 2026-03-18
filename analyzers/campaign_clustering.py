"""Campaign Clustering — groups ad variants into campaigns/concepts."""
import json
from collections import defaultdict
from pathlib import Path
from difflib import SequenceMatcher

def similarity(a: str, b: str) -> float:
    """Quick text similarity ratio."""
    return SequenceMatcher(None, a.lower()[:200], b.lower()[:200]).ratio()

def cluster_ads(ads: list[dict], analysis_results: list[dict] = None) -> dict:
    """
    Cluster ads into campaign groups.
    Returns: {
        "campaigns": [
            {
                "concept": "choose your own workers",
                "advertiser": "Trilogy Care",
                "variant_count": 4,
                "best_variant": {...},
                "variants": [...],
                "avg_score": 75,
                "messaging_angles": [...],
                "longest_running_days": 45,
            }
        ],
        "stats": {"total_ads": N, "total_campaigns": M, "avg_variants": X}
    }
    """
    # Build lookup from analysis results
    analysis_map = {}
    if analysis_results:
        for r in analysis_results:
            src = r.get("source_ad", {})
            key = f"{src.get('source', '')}_{src.get('advertiser', '')}_{src.get('ad_index', '')}"
            analysis_map[key] = r

    # Group by advertiser first
    by_advertiser = defaultdict(list)
    for ad in ads:
        adv = ad.get("advertiser", "Unknown")
        # Normalize
        if "trilogy" in adv.lower(): adv = "Trilogy Care"
        elif "bolton" in adv.lower(): adv = "Bolton Clarke"
        elif "dovida" in adv.lower(): adv = "Dovida"
        elif "hammond" in adv.lower(): adv = "HammondCare"
        by_advertiser[adv].append(ad)

    campaigns = []

    for adv, adv_ads in by_advertiser.items():
        # Try to cluster by campaign_concept from analysis
        concept_groups = defaultdict(list)
        unclustered = []

        for ad in adv_ads:
            key = f"{ad.get('source', '')}_{ad.get('advertiser', '')}_{ad.get('ad_index', '')}"
            analysis = analysis_map.get(key, {})
            concept = analysis.get("campaign_concept", "")

            if concept:
                # Find existing similar concept
                matched = False
                for existing_concept in list(concept_groups.keys()):
                    if similarity(concept, existing_concept) > 0.5:
                        concept_groups[existing_concept].append((ad, analysis))
                        matched = True
                        break
                if not matched:
                    concept_groups[concept].append((ad, analysis))
            else:
                unclustered.append((ad, {}))

        # Cluster unclustered ads by copy similarity
        for ad, analysis in unclustered:
            copy = (ad.get("copy_text") or ad.get("full_text", ""))[:200]
            if not copy:
                concept_groups["Unknown concept"].append((ad, analysis))
                continue

            matched = False
            for concept, items in concept_groups.items():
                if items:
                    ref_copy = (items[0][0].get("copy_text") or items[0][0].get("full_text", ""))[:200]
                    if similarity(copy, ref_copy) > 0.4:
                        items.append((ad, analysis))
                        matched = True
                        break
            if not matched:
                label = copy[:40].strip() + "..."
                concept_groups[label].append((ad, analysis))

        # Build campaign objects
        for concept, items in concept_groups.items():
            scores = [a.get("overall_score", 0) for _, a in items if a.get("overall_score")]
            angles = set()
            for _, a in items:
                for angle in a.get("messaging_angles", []):
                    angles.add(angle)

            # Find best variant
            best = max(items, key=lambda x: x[1].get("overall_score", 0)) if items else (None, {})

            campaigns.append({
                "concept": concept,
                "advertiser": adv,
                "variant_count": len(items),
                "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
                "messaging_angles": list(angles),
                "best_variant_score": best[1].get("overall_score", 0),
                "best_variant_copy": (best[0].get("copy_text") or best[0].get("full_text", ""))[:200] if best[0] else "",
                "variants": [
                    {
                        "library_id": ad.get("library_id", ""),
                        "score": a.get("overall_score", 0),
                        "format": ad.get("ad_format", "unknown"),
                        "copy_preview": (ad.get("copy_text") or ad.get("full_text", ""))[:100],
                    }
                    for ad, a in items
                ],
            })

    # Sort campaigns by variant count (most variants = likely most tested)
    campaigns.sort(key=lambda x: -x["variant_count"])

    return {
        "campaigns": campaigns,
        "stats": {
            "total_ads": len(ads),
            "total_campaigns": len(campaigns),
            "avg_variants": round(len(ads) / max(len(campaigns), 1), 1),
        }
    }
