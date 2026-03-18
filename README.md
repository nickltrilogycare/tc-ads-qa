# TC Ads QA — Support at Home Ad Intelligence Platform

**Live Dashboard:** [nickltrilogycare.github.io/tc-ads-qa](https://nickltrilogycare.github.io/tc-ads-qa/)

Competitive intelligence platform for Trilogy Care's Support at Home advertising. Scrapes, analyzes, and visualizes ads from Facebook Ad Library and Google Ads Transparency Center.

## Quick Start

```bash
# Full run (scrape + analyze + deploy)
cd ~/trilogycare-projects/tc-ads-qa
python3 main.py

# Quick check (Trilogy only, Facebook only)
python3 main.py --quick

# Weekly report with week-over-week tracking
python3 weekly_report.py

# Generate email digest
python3 -c "from reports.email_digest import generate_weekly_digest; generate_weekly_digest()"
```

## Dashboard Features

| Feature | Shortcut | Description |
|---------|----------|-------------|
| CMO Brief | `B` | 30-second executive view — 5 numbers + 3 actions |
| All Ads | — | Browse 766+ ads from 39+ advertisers |
| Gallery View | `G` | Image-only mosaic for fast visual scanning |
| Market Voice | — | SVG chart showing messaging theme distribution |
| Gap Matrix | — | Heatmap showing messaging gaps vs competitors |
| Volume | — | Competitive leaderboard by ad count |
| Actions | — | Prioritized marketing action queue |
| Score Logic | — | Full scoring methodology (6 categories, 100 pts) |
| Insights | `I` | Competitive intelligence drawer |
| Swipe File | `S` | Save ads to named boards (Pinterest-style) |
| Compare | — | Head-to-head ad comparison modal |
| Lightbox | Click image | Full-screen ad preview |
| Export | — | Print-optimized report for Monday meetings |
| Dark Mode | 🌙 | Toggle with localStorage persistence |
| Search | `/` | Full-text search across all ads |
| Sort | — | By score, date, or default |
| Filters | — | Platform, format, score range, freshness |
| Human Review | 👍/👎 | Thumbs up/down on each ad |

## Architecture

```
tc-ads-qa/
├── scrapers/
│   ├── facebook.py      # Facebook Ad Library (Playwright)
│   ├── google.py        # Google Ads Transparency (Playwright)
│   ├── video_scraper.py # Download .mp4 from FB CDN
│   └── landing_page.py  # Capture landing page screenshots
├── analyzers/
│   ├── quality.py       # GPT-4.1 scoring + messaging taxonomy
│   ├── video_analyzer.py # Frame extraction + vision analysis
│   ├── competitive.py   # Competitive comparison
│   ├── competitor_strategy.py # Deep per-competitor strategy
│   ├── messaging_gaps.py # Gap matrix builder
│   ├── campaign_clustering.py # Group ad variants into campaigns
│   ├── ad_history.py    # Freshness tracking (first_seen/last_seen)
│   ├── ad_recommendations.py # Turn off/optimize/keep recommendations
│   └── brief_generator.py # AI creative brief generation
├── reports/
│   ├── dashboard_v2.py  # Main HTML dashboard generator
│   ├── dashboard_addons.py # Compare, export, review, lightbox, shortcuts
│   ├── swipe_boards.py  # Pinterest-style save boards
│   ├── charts.py        # SVG chart generators
│   ├── volume_tracker.py # Competitive volume table
│   ├── action_queue.py  # Prioritized action list
│   ├── executive_view.py # CMO Brief panel
│   └── email_digest.py  # Weekly email summary
├── main.py              # Full pipeline orchestrator
├── weekly_report.py     # Automated weekly run
├── config.py            # Configuration + competitor list
└── data/                # Scraped data + analysis results
```

## Data Sources

- **766+ unique ads** from Facebook Ad Library + Google Ads Transparency Center
- **39+ advertisers** including Trilogy Care + major competitors
- **909 registered providers** in the database
- **3 downloaded video ads** with AI frame-by-frame analysis
- **4 landing page captures** with form/phone audit

## Weekly Schedule

```bash
bash setup_weekly.sh  # Sets up Monday 7am launchd job
```
