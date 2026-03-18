#!/usr/bin/env python3
"""
Ad Creation Pipeline — orchestrates all agents to produce ready-to-publish ads.

Flow:
1. Strategy Agent → decides what ads to create (based on competitive intelligence)
2. Hook Agent → generates 5 hooks per ad
3. Copy Agent → writes full ad copy using best hook + copy framework
4. Visual Brief Agent → creates Higgsfield-ready image/video prompts
5. QA Agent → reviews everything for compliance, brand, quality
6. Output → complete ad packages ready for production

Usage:
  python3 -m ad_creator.pipeline              # Generate 5 new ad campaigns
  python3 -m ad_creator.pipeline --count 3    # Generate 3
  python3 -m ad_creator.pipeline --dry-run    # Strategy only, no copy generation
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ad_creator.strategy_agent import generate_ad_strategy
from ad_creator.hook_agent import generate_hooks
from ad_creator.copy_agent import generate_ad_copy, generate_google_search_copy
from ad_creator.visual_brief_agent import generate_visual_brief
from ad_creator.qa_agent import qa_review


OUTPUT_DIR = Path(__file__).parent.parent / "ad_output"


def run_pipeline(num_ads: int = 5, dry_run: bool = False) -> list[dict]:
    """Run the full ad creation pipeline."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now()

    print("=" * 60)
    print(f"  TC Ad Creator — {now:%d %b %Y %H:%M}")
    print("=" * 60)

    # ── Step 1: Strategy ──
    print("\n[1/5] STRATEGY AGENT")
    print("-" * 40)
    strategies = generate_ad_strategy(num_ads)
    print(f"  Generated {len(strategies)} campaign briefs")
    for s in strategies:
        print(f"  • {s.get('campaign_name', '?')} ({s.get('platform', '?')}, {s.get('format', '?')})")

    if dry_run:
        print("\n  [Dry run — stopping here]")
        return strategies

    # ── Step 2-5: Per-campaign pipeline ──
    results = []
    for i, strategy in enumerate(strategies):
        if "error" in strategy:
            print(f"\n  [!] Skipping errored strategy: {strategy['error']}")
            continue

        campaign_name = strategy.get("campaign_name", f"Campaign {i+1}")
        print(f"\n{'='*50}")
        print(f"  Campaign {i+1}/{len(strategies)}: {campaign_name}")
        print(f"{'='*50}")

        # ── Step 2: Hooks ──
        print(f"\n  [2/5] HOOK AGENT")
        hooks = generate_hooks(strategy, num_hooks=5)
        if hooks and not isinstance(hooks[0], dict) or "error" in hooks[0]:
            print(f"    Error generating hooks")
            hooks = [{"hook_text": strategy.get("hook_brief", ""), "hook_type": "direct_address", "estimated_strength": 5}]
        else:
            # Sort by strength and pick best
            hooks.sort(key=lambda h: h.get("estimated_strength", 0), reverse=True)
            print(f"    Generated {len(hooks)} hooks")
            for h in hooks[:3]:
                print(f"    • [{h.get('hook_type', '?')}] {h.get('hook_text', '')[:60]}... (strength: {h.get('estimated_strength', '?')})")

        best_hook = hooks[0] if hooks else {}

        # ── Step 3: Copy ──
        print(f"\n  [3/5] COPY AGENT")
        platform = strategy.get("platform", "facebook")
        if platform == "google_search":
            ad_copy = [generate_google_search_copy(strategy)]
        else:
            ad_copy = generate_ad_copy(strategy, best_hook)
        if isinstance(ad_copy, dict):
            ad_copy = [ad_copy]
        print(f"    Generated {len(ad_copy)} copy variants")
        for c in ad_copy[:2]:
            if isinstance(c, dict):
                print(f"    • [{c.get('ab_variant', '?')}] {c.get('headline', c.get('primary_text', ''))[:60]}...")

        # ── Step 4: Visual Brief ──
        print(f"\n  [4/5] VISUAL BRIEF AGENT")
        visual = generate_visual_brief(strategy, ad_copy[0] if ad_copy else {})
        if "error" not in visual:
            print(f"    Higgsfield prompt: {visual.get('higgsfield_prompt', '')[:80]}...")
            print(f"    Setting: {visual.get('setting', '')[:60]}")
        else:
            print(f"    Error: {visual.get('error', '')}")

        # ── Step 5: QA Review ──
        print(f"\n  [5/5] QA AGENT")
        qa = qa_review(strategy, hooks, ad_copy, visual)
        verdict = qa.get("overall_verdict", "UNKNOWN")
        score = qa.get("overall_score", 0)
        print(f"    Verdict: {verdict} ({score}/100)")
        if qa.get("revision_suggestions"):
            for rev in qa["revision_suggestions"][:3]:
                print(f"    ⚠ [{rev.get('priority', '?')}] {rev.get('component', '?')}: {rev.get('suggestion', '')[:60]}")

        # Package result
        result = {
            "campaign_name": campaign_name,
            "strategy": strategy,
            "hooks": hooks,
            "best_hook": best_hook,
            "ad_copy": ad_copy,
            "visual_brief": visual,
            "qa_review": qa,
            "created_at": now.isoformat(),
        }
        results.append(result)

    # ── Save output ──
    output_path = OUTPUT_DIR / f"ad_batch_{now:%Y%m%d_%H%M}.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Generate human-readable summary
    summary_path = OUTPUT_DIR / f"ad_batch_{now:%Y%m%d_%H%M}_summary.md"
    summary = generate_summary(results)
    summary_path.write_text(summary)

    print(f"\n{'='*60}")
    print(f"  Pipeline complete!")
    print(f"  {len(results)} campaigns generated")
    print(f"  Output: {output_path}")
    print(f"  Summary: {summary_path}")
    approved = sum(1 for r in results if r.get("qa_review", {}).get("overall_verdict") == "APPROVED")
    needs_rev = sum(1 for r in results if r.get("qa_review", {}).get("overall_verdict") == "NEEDS_REVISION")
    print(f"  QA: {approved} approved, {needs_rev} need revision")
    print(f"{'='*60}\n")

    return results


def generate_summary(results: list[dict]) -> str:
    """Generate a human-readable markdown summary of the ad batch."""
    now = datetime.now()
    md = f"# TC Ad Creator — Batch Summary\n"
    md += f"**Generated:** {now:%d %B %Y %H:%M}\n\n"
    md += f"**Campaigns:** {len(results)}\n\n"

    for i, r in enumerate(results, 1):
        s = r.get("strategy", {})
        qa = r.get("qa_review", {})
        hook = r.get("best_hook", {})
        copy = r.get("ad_copy", [{}])
        visual = r.get("visual_brief", {})

        verdict = qa.get("overall_verdict", "?")
        verdict_emoji = "✅" if verdict == "APPROVED" else "⚠️" if verdict == "NEEDS_REVISION" else "❌"

        md += f"---\n\n## {i}. {s.get('campaign_name', '?')} {verdict_emoji}\n\n"
        md += f"**Platform:** {s.get('platform', '?')} | **Format:** {s.get('format', '?')} | **Objective:** {s.get('objective', '?')}\n"
        md += f"**Messaging Angle:** {s.get('messaging_angle', '?')}\n"
        md += f"**QA Score:** {qa.get('overall_score', '?')}/100\n\n"

        md += f"### Hook\n> {hook.get('hook_text', 'N/A')}\n\n"

        if copy and isinstance(copy[0], dict):
            c = copy[0]
            md += f"### Ad Copy (Variant A)\n"
            md += f"**Headline:** {c.get('headline', 'N/A')}\n\n"
            md += f"**Primary Text:** {c.get('primary_text', 'N/A')}\n\n"
            md += f"**CTA:** {c.get('cta_button', 'N/A')}\n\n"

        md += f"### Visual Direction\n"
        md += f"{visual.get('scene_description', visual.get('higgsfield_prompt', 'N/A'))}\n\n"

        if qa.get("revision_suggestions"):
            md += f"### QA Notes\n"
            for rev in qa["revision_suggestions"]:
                md += f"- **[{rev.get('priority', '?')}]** {rev.get('suggestion', '')}\n"
            md += "\n"

    return md


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TC Ad Creator Pipeline")
    parser.add_argument("--count", type=int, default=5, help="Number of ad campaigns to generate")
    parser.add_argument("--dry-run", action="store_true", help="Strategy only, no copy generation")
    args = parser.parse_args()

    run_pipeline(num_ads=args.count, dry_run=args.dry_run)
