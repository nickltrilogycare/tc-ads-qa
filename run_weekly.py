#!/usr/bin/env python3
"""
Full Weekly Pipeline — runs everything end-to-end:
1. Scrape all advertisers (FB + Google)
2. Update ad history
3. Analyze new/changed ads with GPT-4.1
4. Build messaging gap matrix
5. Generate dashboard + deploy to GitHub Pages
6. Generate email digest
"""
import sys
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import DATA_DIR, REPORTS_DIR, SCREENSHOTS_DIR
from scrapers.facebook import scrape_facebook_ads
from scrapers.google import scrape_google_ads
from analyzers.ad_history import update_history, get_freshness_stats
from analyzers.messaging_gaps import build_messaging_matrix, find_gaps
from reports.dashboard_v2 import generate_dashboard_v2, is_sah_relevant


def ensure_dirs():
    for d in [DATA_DIR, REPORTS_DIR, SCREENSHOTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def run():
    ensure_dirs()
    now = datetime.now()
    print(f"\n{'='*60}")
    print(f"  TC Ads QA — Weekly Pipeline — {now:%d %b %Y %H:%M}")
    print(f"{'='*60}")

    # ── Step 1: Scrape ──
    print("\n[1/5] SCRAPING")

    # Core searches
    searches = [
        ("trilogy care support at home", "TrilogyCare"),
        ("bolton clarke support at home", "BoltonClarke"),
        ("dovida support at home", "Dovida"),
        ("support at home aged care", "SAH_broad"),
        ("home care package provider", "HCP"),
        ("self managed home care australia", "SelfManaged"),
        ("Five Good Friends home care", "FiveGoodFriends"),
        ("Prestige Inhome Care", "PrestigeInhome"),
        ("Feros Care", "FerosCare"),
        ("Australian Unity home care", "AustralianUnity"),
        ("Anglicare home care", "Anglicare"),
        ("Uniting AgeWell", "UnitingAgeWell"),
        ("Right at Home Australia", "RightAtHome"),
        ("Nurse Next Door Australia", "NurseNextDoor"),
        ("Pearl Home Care", "PearlHomeCare"),
    ]

    all_ads = []
    for query, label in searches:
        ads = scrape_facebook_ads(query, label, max_ads=20)
        all_ads.extend(ads)

    # Also get Google ads for Trilogy
    g_ads = scrape_google_ads("Trilogy Care", "TrilogyCare", max_ads=15)
    all_ads.extend(g_ads)

    print(f"\n  Total scraped: {len(all_ads)}")

    # ── Step 2: Update History ──
    print("\n[2/5] UPDATING AD HISTORY")
    update_history(all_ads)
    stats = get_freshness_stats()
    print(f"  History: {stats}")

    # ── Step 3: Load all data ──
    print("\n[3/5] LOADING ALL DATA")
    # Combine with existing data
    for f in DATA_DIR.glob("*.json"):
        if "history" in f.name or "full_results" in f.name or "messaging" in f.name:
            continue
        try:
            data = json.loads(f.read_text())
            if isinstance(data, dict):
                for ads in data.values():
                    if isinstance(ads, list):
                        all_ads.extend(ads)
        except Exception:
            pass

    # Dedup
    seen = set()
    deduped = []
    for ad in all_ads:
        lid = ad.get("library_id", "")
        key = lid if lid else f"{ad.get('source','')}_{ad.get('advertiser','')}_{ad.get('ad_index','')}"
        if key not in seen:
            seen.add(key)
            deduped.append(ad)

    print(f"  {len(deduped)} unique ads")

    # ── Step 4: Build gap matrix ──
    print("\n[4/5] BUILDING MESSAGING GAP MATRIX")
    sah = [a for a in deduped if is_sah_relevant(a)]
    try:
        # Load existing analysis results
        analysis_file = sorted(DATA_DIR.glob("full_results_*.json"), reverse=True)
        if analysis_file:
            analysis = json.loads(analysis_file[0].read_text())
            all_results = analysis.get("trilogy_results", [])
            for v in analysis.get("competitor_results", {}).values():
                all_results.extend(v)
        else:
            all_results = []

        matrix = build_messaging_matrix(sah, all_results)
        gaps_result = find_gaps(matrix)
        json.dump({"matrix": matrix, "gaps": gaps_result},
                  open(DATA_DIR / "messaging_gaps.json", "w"), indent=2, default=str)
        print(f"  Gaps found: {len(gaps_result.get('gaps', []))}")
    except Exception as e:
        print(f"  Gap matrix error: {e}")
        all_results = []
        analysis = {"competitive_analysis": {}}

    # ── Step 5: Generate Dashboard ──
    print("\n[5/5] GENERATING DASHBOARD")
    competitive = analysis.get("competitive_analysis", {}) if "analysis" in dir() else {}
    path = generate_dashboard_v2(deduped, all_results, competitive, sah_only=True)

    # Copy to docs for GitHub Pages
    docs_path = Path(__file__).parent / "docs" / "index.html"
    shutil.copy(str(path), str(docs_path))
    print(f"  Dashboard: {path}")

    # Git push
    try:
        subprocess.run(["git", "add", "-A"], cwd=str(Path(__file__).parent), check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Weekly update: {now:%Y-%m-%d} — {len(deduped)} ads"],
            cwd=str(Path(__file__).parent), check=False,
        )
        subprocess.run(["git", "push", "origin", "main"],
                        cwd=str(Path(__file__).parent), check=False)
        print("  Pushed to GitHub Pages")
    except Exception as e:
        print(f"  Git push error: {e}")

    # Generate email digest
    try:
        from reports.email_digest import generate_weekly_digest
        generate_weekly_digest()
    except Exception as e:
        print(f"  Digest error: {e}")

    print(f"\n{'='*60}")
    print(f"  Done! Dashboard live at:")
    print(f"  https://nickltrilogycare.github.io/tc-ads-qa/")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run()
