"""A/B Test Detector — finds ad variants being tested by each advertiser."""
from difflib import SequenceMatcher
from collections import defaultdict


def detect_ab_tests(ads: list[dict], similarity_threshold: float = 0.6) -> list[dict]:
    """
    Find groups of ads that appear to be A/B test variants.
    Returns list of test groups with variants and differences highlighted.
    """
    # Group by advertiser first
    by_adv = defaultdict(list)
    for ad in ads:
        adv = ad.get("advertiser", "Unknown")
        by_adv[adv].append(ad)

    tests = []

    for adv, adv_ads in by_adv.items():
        # Compare each pair
        used = set()
        for i, ad1 in enumerate(adv_ads):
            if i in used:
                continue
            copy1 = (ad1.get("copy_text") or ad1.get("full_text", ""))[:300]
            if not copy1:
                continue

            group = [ad1]
            for j, ad2 in enumerate(adv_ads[i + 1 :], i + 1):
                if j in used:
                    continue
                copy2 = (ad2.get("copy_text") or ad2.get("full_text", ""))[:300]
                if not copy2:
                    continue

                sim = SequenceMatcher(None, copy1.lower(), copy2.lower()).ratio()
                if sim >= similarity_threshold and sim < 0.95:  # Similar but not identical
                    group.append(ad2)
                    used.add(j)

            if len(group) >= 2:
                used.add(i)
                # Find what's different
                copies = [
                    (ad.get("copy_text") or ad.get("full_text", ""))[:200]
                    for ad in group
                ]

                tests.append(
                    {
                        "advertiser": adv,
                        "variant_count": len(group),
                        "variants": [
                            {
                                "library_id": ad.get("library_id", ""),
                                "copy_preview": (
                                    ad.get("copy_text") or ad.get("full_text", "")
                                )[:150],
                                "format": ad.get("ad_format", ""),
                                "cta": ad.get("cta", ""),
                            }
                            for ad in group
                        ],
                        "test_type": "copy_variant",
                    }
                )

    tests.sort(key=lambda x: -x["variant_count"])
    return tests
