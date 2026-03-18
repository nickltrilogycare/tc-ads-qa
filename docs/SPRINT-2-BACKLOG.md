# TC Ads QA — Sprint 2 Backlog

**Sprint Goal:** Transform from a reporting tool into an interactive intelligence platform with temporal trends, gap analysis, and human-in-the-loop review.

**Prioritization:** Ordered by (Impact x Differentiation) / Effort. Every feature below directly addresses Sprint 1 user feedback and creates defensible distance from generic ad-spy tools.

---

## S2-01: Messaging Gap Matrix (CMO request — highest strategic value)

**User Story:**
> As the CMO, I want to see a matrix of messaging angles (rows) vs advertisers (columns) so I can instantly identify which competitor themes Trilogy is NOT using, and which angles are uncontested whitespace.

**Why it matters:**
No ad-spy tool does this. Foreplay/MagicBrief show you ads — they don't tell you what you're *not* saying. This turns the quality-scored messaging taxonomy from Sprint 1 into an actionable strategic map. Nick explicitly asked for this.

**Implementation Spec:**

1. **New analyzer: `analyzers/messaging_gaps.py`**
   - Input: all ads (Trilogy + competitors), each already tagged with `messaging_angles[]` from Sprint 1's quality analyzer
   - Build a matrix: `{angle: {advertiser: count}}` across all 10 taxonomy categories
   - Compute three derived views:
     - **Gap Angles**: angles where `Trilogy count == 0` but `competitor count > 0` — these are blind spots
     - **Uncontested Angles**: angles where `competitor count == 0` but opportunity exists — these are whitespace
     - **Crowded Angles**: angles where 4+ competitors are active — red ocean
   - For each gap angle, extract the top 3 competitor ad copy snippets as inspiration (copy_text[:200])
   - Output JSON: `{"matrix": {...}, "gaps": [...], "whitespace": [...], "crowded": [...], "inspiration": {...}}`

2. **New chart: `reports/charts.py` — add `messaging_gap_matrix_svg()`**
   - Heatmap-style SVG: rows = 10 messaging angles, columns = advertisers
   - Cell color intensity = ad count (darker = more ads using that angle)
   - Trilogy column highlighted with a distinct border
   - Gap cells (Trilogy = 0, competitors > 0) shown with a red warning icon
   - Whitespace cells shown with a green opportunity icon
   - Below the heatmap: "Gap Alert" callout box listing the top 3 gaps with competitor example copy

3. **Dashboard integration: `reports/dashboard_v2.py`**
   - New tab in header nav: "Messaging Gaps"
   - Renders the heatmap SVG inline
   - Below the heatmap: expandable cards for each gap angle showing:
     - Which competitors use this angle (with count)
     - Sample ad copy from each competitor
     - Suggested brief: "Trilogy could test [angle] messaging — competitors [X, Y] are using this with copy like: '...'"
   - Export: the gap matrix prints as a clean table in the print/export view

4. **Data flow:**
   - `main.py` Step 4 calls `analyze_messaging_gaps(trilogy_ads, competitor_ads)` after quality scoring
   - Results passed into `generate_dashboard_v2()` as new `messaging_gaps` parameter
   - Stored in `full_results_*.json` under `"messaging_gaps"` key

**Complexity:** Medium (2-3 days)
- Analyzer logic: straightforward aggregation over existing `messaging_angles` tags — no new API calls
- SVG heatmap: moderate (new chart type, but pattern established in `charts.py`)
- Dashboard wiring: routine (follows existing addon pattern)

**Impact:** Very High
- Directly answers CMO's #1 request
- Unique capability — no competitor tool provides messaging gap analysis for aged care
- Drives real creative briefs, not just reporting

---

## S2-02: Ad Volume Trend Lines (Media Buyer request — temporal intelligence)

**User Story:**
> As a Media Buyer, I want to see how each competitor's ad volume has changed over the past 8+ weeks so I can spot who's scaling up spend, who's pulling back, and time our own campaign pushes accordingly.

**Why it matters:**
Ad history tracking from Sprint 1 stores `first_seen`/`last_seen` per ad per scan. Trend lines turn that static snapshot into a time series. This is competitive media intelligence — when a competitor ramps from 5 to 25 active ads in a fortnight, that signals a new campaign push.

**Implementation Spec:**

1. **New analyzer: `analyzers/trend_tracker.py`**
   - Input: `data/ad_history.json` (cumulative across all runs)
   - For each weekly scan date, count active ads per advertiser:
     ```
     {
       "2026-03-04": {"Trilogy Care": 12, "Bolton Clarke": 8, ...},
       "2026-03-11": {"Trilogy Care": 14, "Bolton Clarke": 15, ...},
       ...
     }
     ```
   - Compute derived metrics per advertiser:
     - `trend`: "ramping_up" | "stable" | "declining" (based on 3-week moving average)
     - `velocity`: ads added per week (net new - stopped)
     - `churn_rate`: % of ads that stopped in the last 2 weeks
   - Detect "surge alerts": any competitor whose active ad count increased 50%+ week-over-week
   - Output: `{"weekly_counts": {...}, "trends": {...}, "surge_alerts": [...]}`

2. **New chart: `reports/charts.py` — add `ad_volume_trend_svg()`**
   - Multi-line SVG chart: X axis = weeks, Y axis = active ad count
   - One line per advertiser, Trilogy Care line thicker and in brand blue
   - Hover data points via `<title>` elements (native SVG tooltip)
   - Surge alert markers: red dot on any week where a competitor surged
   - Y axis auto-scaled, X axis shows date labels

3. **Dashboard integration:**
   - New tab: "Trends"
   - Renders the trend line SVG at full width
   - Below: "Trend Summary" cards per advertiser showing:
     - Current active ads count
     - Trend direction arrow (up/down/flat)
     - Velocity (e.g., "+4 ads/week")
     - Surge alert badge if applicable
   - Filter by advertiser (checkboxes to toggle lines on/off)

4. **Data dependency:**
   - Requires `setup_weekly.sh` to have run at least 3-4 times to generate meaningful trend data
   - First run: show "Collecting data — trends available after 3 weekly scans" placeholder
   - Store weekly snapshots in `data/weekly_snapshots/YYYY-MM-DD.json`

**Complexity:** Medium (2-3 days)
- Aggregation logic: moderate (time-bucketing ad history entries)
- SVG line chart: moderate (new chart type, multi-line with tooltips)
- Weekly snapshot persistence: simple file I/O

**Impact:** High
- Media buyers live on this data — it's the "when to act" signal
- Reveals competitor budget patterns (ramp = new campaign, decline = budget cut or creative fatigue)
- Builds compounding value over time (more data = better trends)

---

## S2-03: Lightbox + Filmstrip Comparison View (Creative Director + PM requests)

**User Story:**
> As a Creative Director, I want to click any ad image and see it full-screen in a lightbox, then use arrow keys to browse. I also want a "filmstrip" mode that shows ALL video ads from two selected advertisers side-by-side for rapid creative comparison.

**Why it matters:**
Two Sprint 1 feedback items in one feature. The PM wants full-screen image viewing (instead of jumping to Facebook). The Creative Director wants to compare entire creative libraries, not just 2 ads. This is the "Foreplay swipe file on steroids" — purpose-built for competitive creative review sessions.

**Implementation Spec:**

1. **Lightbox overlay (in `reports/dashboard_addons.py` — new function `get_lightbox_html()`)**
   - Clicking any ad image opens a full-screen dark overlay with:
     - The ad image centered and scaled to fit viewport
     - Left/right arrow navigation (keyboard + click)
     - Ad metadata bar at bottom: advertiser name, score pill, messaging angle tags, CTA
     - Close on Escape or click outside
   - Images cycle through all visible (non-filtered) ads in current view order
   - Replaces the current `onclick="window.open(fb_url)"` on `.card-creative`
   - "View on Facebook" link still available as a text link in the metadata bar

2. **Filmstrip comparison mode (in `reports/dashboard_addons.py` — new function `get_filmstrip_html()`)**
   - Activated from a new "Filmstrip Compare" button in the toolbar
   - Two-pane layout:
     - Left pane: select Advertiser A from dropdown, shows scrollable vertical strip of all their ad creatives (thumbnails, 200px wide)
     - Right pane: select Advertiser B, same layout
     - Header shows count: "Trilogy Care (14 ads) vs Bolton Clarke (11 ads)"
   - Each thumbnail shows: image, format badge (VIDEO/IMAGE), score pill, first 1 line of copy
   - Click any thumbnail in either pane to expand it in the lightbox
   - Filter controls within each pane: format (video/image/text), score range
   - Useful for creative review meetings: "show me all our video work vs theirs"

3. **Dashboard wiring:**
   - `dashboard_v2.py`: change `.card-creative onclick` to call `openLightbox(cardIndex)` instead of `window.open()`
   - Add `get_lightbox_html()` and `get_filmstrip_html()` output to the page HTML
   - Add "Filmstrip" button to toolbar `.view-btns` group
   - Card data array (already built as `cards[]` in Python) serialized to a `<script>` tag as `window.AD_CARDS = [...]` for JS access

**Complexity:** Medium-High (3-4 days)
- Lightbox: well-understood pattern, 1 day
- Filmstrip two-pane: moderate UI complexity, 2 days
- Arrow key navigation + filtering within filmstrip: 1 day

**Impact:** High
- Directly addresses 2 user feedback items
- The filmstrip mode is genuinely unique — no ad-spy tool lets you compare full creative libraries side-by-side
- Makes creative review meetings dramatically faster

---

## S2-04: Human Review Layer (Thumbs Up/Down + Notes) (Head of Digital request)

**User Story:**
> As the Head of Digital, I want to add a thumbs-up or thumbs-down to any ad and optionally leave a note, so we can calibrate the AI scores against human judgment and build an internal "approved" library of reference ads.

**Why it matters:**
AI scores are useful but subjective. Human review creates a feedback loop: over time, you can compare AI vs human scores to identify where the model over/under-rates. More importantly, the "thumbs up" ads become a curated swipe file — the Creative Director can filter to "human-approved" ads only for inspiration. This is the beginning of a collaborative workflow layer.

**Implementation Spec:**

1. **New data store: `data/human_reviews.json`**
   - Schema per review:
     ```json
     {
       "library_id": "123456",
       "reviewer": "nick",
       "rating": "up" | "down" | null,
       "note": "Great use of empowerment messaging, strong CTA",
       "reviewed_at": "2026-03-18T14:30:00",
       "tags": ["reference", "brief-inspiration"]
     }
     ```
   - One entry per (library_id, reviewer) pair — latest review wins
   - File-based storage (no backend needed — single user tool for now)

2. **Dashboard UI (in `reports/dashboard_addons.py` — new function `get_review_html()`)**
   - Each ad card footer gets two new buttons: thumbs-up (green) and thumbs-down (red)
   - Clicking either opens a small inline popover with:
     - The selected rating (toggleable)
     - A text input for optional note (max 280 chars)
     - Tag checkboxes: "Reference Ad", "Brief Inspiration", "Compliance Risk", "Needs Refresh"
     - "Save" button
   - Saved reviews persist to `localStorage` immediately (for instant UI update)
   - On page load, reviews loaded from `localStorage` and applied to cards
   - Export/sync: a "Save Reviews" button in the header writes `localStorage` data to `data/human_reviews.json` via a download blob (no server needed)

3. **Review indicators on cards:**
   - Reviewed cards show a small badge: green check (thumbs up) or red X (thumbs down)
   - New filter chip in toolbar: "Human Approved" (shows only thumbs-up ads)
   - New filter chip: "Needs Review" (shows only un-reviewed ads)
   - In the lightbox (S2-03), show the human review status alongside the AI score

4. **AI vs Human calibration report (stretch):**
   - After 20+ reviews, show a small chart: AI score (X axis) vs Human rating (Y axis binary)
   - Highlights disagreements: "AI scored 82 but human gave thumbs-down" — these are learning opportunities

**Complexity:** Medium (2-3 days)
- localStorage-based review: simple, 1 day
- UI buttons + popover: 1 day
- Filter integration + calibration chart: 1 day

**Impact:** High
- Transforms the tool from "AI tells you" to "AI + human agree"
- Creates a curated swipe file that compounds in value over time
- Calibration data could eventually fine-tune the scoring prompts
- Addresses the Head of Digital's exact concern about AI-only scoring

---

## S2-05: New Ad Watchlist with Change Detection (Marketing Coordinator request)

**User Story:**
> As a Marketing Coordinator, I want to set up a watchlist of specific competitors and get a summary of new/changed/stopped ads each time the tool runs, so I can brief the team without manually scanning the full dashboard.

**Why it matters:**
The tool currently requires opening the dashboard and manually looking for changes. A watchlist with change detection turns it into a proactive monitoring system. The Marketing Coordinator runs the tool weekly — they need a "what changed since last time" summary, not a full audit. This also lays the groundwork for email/Slack alerts in Sprint 3.

**Implementation Spec:**

1. **Watchlist config: `data/watchlist.json`**
   - Schema:
     ```json
     {
       "watched_advertisers": ["Bolton Clarke", "HomeMade", "Dovida (Home Instead)"],
       "alert_on": {
         "new_ads": true,
         "stopped_ads": true,
         "messaging_shift": true,
         "volume_surge": true
       },
       "last_run": "2026-03-11T09:00:00"
     }
     ```
   - Editable from the dashboard UI (settings modal) or directly in the JSON file

2. **Change detection engine: `analyzers/change_detector.py`**
   - Compare current scan results against `data/ad_history.json` and previous `full_results_*.json`
   - Detect and categorize changes:
     - **New Ads**: `first_seen == today` for watched advertisers
     - **Stopped Ads**: status changed from `active` to `stopped` since last run
     - **Messaging Shifts**: advertiser's top messaging angle changed (e.g., was "cost_transparency", now "empowerment_control")
     - **Creative Format Shifts**: advertiser switched from mostly image to mostly video
     - **Volume Changes**: significant increase/decrease in active ad count
   - Output: `{"changes": [...], "summary": "...", "urgency": "low|medium|high"}`
   - Generate a natural-language summary via GPT-4.1: "Since your last scan on 11 Mar, Bolton Clarke launched 6 new ads focused on government transition messaging. HomeMade stopped 3 ads and appears to be shifting toward video."

3. **Dashboard integration:**
   - New "Watchlist" tab in header nav
   - Shows a timeline of changes, most recent first
   - Each change entry: advertiser avatar, change type badge, description, timestamp
   - "This Week's Changes" summary card at top with key metrics:
     - New ads across watched competitors: X
     - Stopped ads: Y
     - New messaging angles detected: Z
   - Settings modal (gear icon): add/remove advertisers from watchlist, toggle alert types

4. **Terminal output on run:**
   - `main.py` prints a "WATCHLIST ALERT" section at the end of each run:
     ```
     ══════════════════════════════════
       WATCHLIST ALERTS (3 changes)
     ──────────────────────────────────
       NEW  Bolton Clarke: 6 new ads (govt transition focus)
       STOP HomeMade: 3 ads stopped
       SHIFT Dovida: now leading with video (was 20%, now 60%)
     ══════════════════════════════════
     ```
   - This gives the Marketing Coordinator immediate actionable info without opening the dashboard

5. **Future Sprint 3 extension points:**
   - Email digest (send the summary to a distribution list)
   - Slack webhook (post to #marketing-intelligence channel)
   - Threshold-based alerts (only alert if >5 new competitor ads)

**Complexity:** Medium (2-3 days)
- Change detection logic: moderate (diffing current vs previous scan)
- GPT-4.1 summary: 1 API call, reuses existing Azure OpenAI client
- Dashboard timeline UI: 1 day
- Terminal output: trivial

**Impact:** High
- Converts the tool from "pull" (open dashboard) to "push" (tool tells you what changed)
- Marketing Coordinator's exact request — proactive monitoring without manual work
- Watchlist config is the seed for a proper alerting system in Sprint 3
- Change detection compounds with ad history: the longer you run it, the richer the change narrative

---

## Sprint 2 Summary

| # | Feature | Complexity | Impact | User Request |
|---|---------|-----------|--------|-------------|
| S2-01 | Messaging Gap Matrix | Medium (2-3d) | Very High | CMO: "Show me what competitors say that we don't" |
| S2-02 | Ad Volume Trend Lines | Medium (2-3d) | High | Media Buyer: "Who's ramping up, who's cutting back?" |
| S2-03 | Lightbox + Filmstrip Compare | Med-High (3-4d) | High | Creative Dir + PM: full-screen images, cross-library compare |
| S2-04 | Human Review Layer | Medium (2-3d) | High | Head of Digital: "Can we add human review?" |
| S2-05 | New Ad Watchlist | Medium (2-3d) | High | Marketing Coordinator: "Alert me when new competitor ads appear" |

**Total estimated effort:** 12-16 days (2-week sprint with buffer)

**What we're NOT doing in Sprint 2 (parked for Sprint 3):**
- Geographic targeting overlap (Sales team request) — requires geo data from Meta API which is not available in Ad Library scraping; needs research on alternative data sources
- Email/Slack alert delivery — watchlist (S2-05) builds the detection engine; delivery channels come next sprint
- Provider database scaling to 909 providers — current architecture handles ~30 advertisers per run; need to design batch/queue system before scaling 30x

**Dependencies:**
- S2-01 depends on Sprint 1's `messaging_angles` tags being populated in quality analysis results
- S2-02 depends on `ad_history.json` having at least 3 weekly data points for meaningful trends
- S2-03 is independent (pure frontend)
- S2-04 is independent (pure frontend + localStorage)
- S2-05 depends on `ad_history.json` and existing scraper outputs
