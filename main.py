#!/usr/bin/env python3
"""
TC Ads QA Tool — Main Orchestrator
Multi-agent approach to scrape, analyse, and report on Trilogy Care ads
and competitor ads across Facebook Ad Library & Google Ads Transparency Center.

Usage:
  python3 main.py                  # Full run (Trilogy + competitors, both platforms)
  python3 main.py --trilogy-only   # Just Trilogy Care ads
  python3 main.py --quick          # Trilogy only, Facebook only, skip competitors
  python3 main.py --competitors    # Competitor-focused analysis
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    TRILOGY_FACEBOOK_PAGE_ID,
    TRILOGY_GOOGLE_ADVERTISER_QUERY,
    COMPETITORS,
    DATA_DIR,
    REPORTS_DIR,
    SCREENSHOTS_DIR,
)
from scrapers.facebook import scrape_facebook_ads
from scrapers.google import scrape_google_ads
from analyzers.quality import analyze_all_ads, flag_poor_quality
from analyzers.competitive import run_competitive_analysis
from reports.generator import generate_html_report, print_terminal_summary
from reports.dashboard import generate_dashboard


def ensure_dirs():
    for d in [DATA_DIR, REPORTS_DIR, SCREENSHOTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def scrape_trilogy(platforms: list[str] = None) -> list[dict]:
    """Scrape Trilogy Care ads from specified platforms."""
    platforms = platforms or ["facebook", "google"]
    all_ads = []

    if "facebook" in platforms:
        fb_ads = scrape_facebook_ads(TRILOGY_FACEBOOK_PAGE_ID, "TrilogyCare")
        all_ads.extend(fb_ads)

    if "google" in platforms:
        g_ads = scrape_google_ads(TRILOGY_GOOGLE_ADVERTISER_QUERY, "TrilogyCare")
        all_ads.extend(g_ads)

    return all_ads


def scrape_competitors(
    competitor_names: list[str] = None,
    platforms: list[str] = None,
) -> dict[str, list[dict]]:
    """Scrape competitor ads. Returns {name: [ads]}."""
    platforms = platforms or ["facebook", "google"]
    targets = competitor_names or list(COMPETITORS.keys())
    results = {}

    for name in targets:
        comp = COMPETITORS.get(name, {})
        if not comp:
            print(f"  [!] Unknown competitor: {name}")
            continue

        ads = []
        safe_name = name.replace(" ", "_").replace("(", "").replace(")", "")

        if "facebook" in platforms:
            fb_ads = scrape_facebook_ads(comp["facebook_page"], safe_name)
            ads.extend(fb_ads)

        if "google" in platforms:
            g_ads = scrape_google_ads(comp["google_query"], safe_name)
            ads.extend(g_ads)

        results[name] = ads

    return results


def run_full_pipeline(
    include_competitors: bool = True,
    platforms: list[str] = None,
    competitor_names: list[str] = None,
    quality_threshold: int = 50,
) -> Path:
    """
    Full pipeline: scrape → analyse → compare → report.
    Returns path to the generated HTML report.
    """
    ensure_dirs()
    platforms = platforms or ["facebook", "google"]

    print("=" * 60)
    print(f"  TC Ads QA Tool — {datetime.now():%d %b %Y %H:%M}")
    print("=" * 60)

    # ── Step 1: Scrape ──
    print("\n[1/4] SCRAPING ADS")
    print("-" * 40)

    print("\n▶ Trilogy Care")
    trilogy_ads = scrape_trilogy(platforms)

    competitor_ads = {}
    if include_competitors:
        print("\n▶ Competitors")
        competitor_ads = scrape_competitors(competitor_names, platforms)

    total_scraped = len(trilogy_ads) + sum(len(v) for v in competitor_ads.values())
    print(f"\n  Total ads scraped: {total_scraped}")

    # ── Step 2: Analyse Trilogy Ads ──
    print("\n[2/4] ANALYSING TRILOGY ADS")
    print("-" * 40)

    if trilogy_ads:
        trilogy_results = analyze_all_ads(trilogy_ads)
    else:
        print("  No Trilogy ads found to analyse")
        trilogy_results = []

    # ── Step 3: Analyse Competitor Ads ──
    print("\n[3/4] ANALYSING COMPETITOR ADS")
    print("-" * 40)

    competitor_results = {}
    if include_competitors and competitor_ads:
        for name, ads in competitor_ads.items():
            if ads:
                print(f"\n  ▶ {name}")
                competitor_results[name] = analyze_all_ads(ads)
            else:
                competitor_results[name] = []
    else:
        print("  Skipping competitor analysis")

    # ── Step 4: Competitive Comparison & Report ──
    print("\n[4/4] GENERATING REPORT")
    print("-" * 40)

    # Run competitive analysis
    competitive_analysis = {}
    if trilogy_ads and competitor_ads:
        print("  Running competitive analysis...")
        competitive_analysis = run_competitive_analysis(trilogy_ads, competitor_ads)
    else:
        competitive_analysis = {
            "executive_summary": "Limited data available — competitive analysis requires both Trilogy and competitor ads.",
            "recommendations": [],
        }

    # Flag poor quality
    poor = flag_poor_quality(trilogy_results, quality_threshold)
    if poor:
        print(f"\n  ⚠ {len(poor)} poor quality ads detected (score < {quality_threshold})")

    # Generate reports
    report_path = generate_html_report(
        trilogy_results,
        competitor_results,
        competitive_analysis,
    )

    # Generate visual dashboard
    all_ads = trilogy_ads + [ad for ads in competitor_ads.values() for ad in ads]
    all_results = trilogy_results + [r for results in competitor_results.values() for r in results]
    dashboard_path = generate_dashboard(all_ads, all_results, competitive_analysis)

    # Terminal summary
    print_terminal_summary(trilogy_results, competitive_analysis)

    # Save raw results
    raw_path = DATA_DIR / f"full_results_{datetime.now():%Y%m%d_%H%M}.json"
    with open(raw_path, "w") as f:
        json.dump({
            "run_date": datetime.now().isoformat(),
            "trilogy_results": trilogy_results,
            "competitor_results": {k: v for k, v in competitor_results.items()},
            "competitive_analysis": competitive_analysis,
            "poor_quality_ads": poor,
        }, f, indent=2, default=str)

    print(f"\n  Raw data: {raw_path}")
    print(f"  HTML report: {report_path}")
    print(f"  Visual dashboard: {dashboard_path}")
    print(f"\n{'=' * 60}")
    print(f"  Done! Open the dashboard:")
    print(f"  open \"{dashboard_path}\"")
    print(f"{'=' * 60}\n")

    return dashboard_path


def main():
    parser = argparse.ArgumentParser(description="TC Ads QA Tool")
    parser.add_argument("--trilogy-only", action="store_true", help="Only analyse Trilogy Care ads")
    parser.add_argument("--quick", action="store_true", help="Quick run: Trilogy only, Facebook only")
    parser.add_argument("--competitors", action="store_true", help="Focus on competitor analysis")
    parser.add_argument("--facebook-only", action="store_true", help="Only scrape Facebook")
    parser.add_argument("--google-only", action="store_true", help="Only scrape Google")
    parser.add_argument("--competitor-names", nargs="+", help="Specific competitors to analyse")
    parser.add_argument("--threshold", type=int, default=50, help="Quality score threshold for flagging")
    args = parser.parse_args()

    platforms = ["facebook", "google"]
    if args.facebook_only:
        platforms = ["facebook"]
    elif args.google_only:
        platforms = ["google"]
    elif args.quick:
        platforms = ["facebook"]

    include_competitors = not (args.trilogy_only or args.quick)

    dashboard_path = run_full_pipeline(
        include_competitors=include_competitors,
        platforms=platforms,
        competitor_names=args.competitor_names,
        quality_threshold=args.threshold,
    )

    # Auto-open on macOS
    import subprocess
    subprocess.run(["open", str(dashboard_path)], check=False)


if __name__ == "__main__":
    main()
