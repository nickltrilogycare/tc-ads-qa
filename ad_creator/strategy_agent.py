"""
Strategy Agent — decides WHAT ads to create based on competitive intelligence.
Reads messaging gaps, competitor analysis, and brand context to produce an ad brief.
"""
import json
from pathlib import Path
from openai import AzureOpenAI
from config import (
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_API_VERSION,
)
from ad_creator.brand_context import BRAND, COPY_FRAMEWORKS

DATA_DIR = Path(__file__).parent.parent / "data"


def get_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
    )


def load_intelligence() -> dict:
    """Load all competitive intelligence for strategy decisions."""
    intel = {}

    # Messaging gaps
    try:
        intel["messaging_gaps"] = json.loads((DATA_DIR / "messaging_gaps.json").read_text())
    except Exception:
        intel["messaging_gaps"] = {}

    # Messaging distribution
    try:
        intel["messaging_analysis"] = json.loads((DATA_DIR / "messaging_analysis.json").read_text())
    except Exception:
        intel["messaging_analysis"] = {}

    # Campaign clusters
    try:
        intel["campaigns"] = json.loads((DATA_DIR / "campaign_clusters.json").read_text())
    except Exception:
        intel["campaigns"] = {}

    # A/B tests
    try:
        intel["ab_tests"] = json.loads((DATA_DIR / "ab_tests.json").read_text())
    except Exception:
        intel["ab_tests"] = []

    # Video analyses
    try:
        intel["video_analyses"] = json.loads((DATA_DIR / "video_analyses.json").read_text())
    except Exception:
        intel["video_analyses"] = []

    return intel


def generate_ad_strategy(num_ads: int = 5) -> list[dict]:
    """
    Produce a strategic ad brief — which ads to create, targeting which gaps.
    Returns a list of ad briefs ready for the Hook + Copy agents.
    """
    client = get_client()
    intel = load_intelligence()

    # Build intelligence summary
    gaps = intel.get("messaging_gaps", {}).get("gaps", {}).get("gaps", [])
    msg_dist = intel.get("messaging_analysis", {}).get("messaging_distribution", {})
    trilogy_share = intel.get("messaging_analysis", {}).get("trilogy_share", {})

    intel_summary = f"""
MESSAGING GAPS (Trilogy under-represented):
{json.dumps(gaps[:5], indent=2) if gaps else "No gaps identified"}

MARKET MESSAGING DISTRIBUTION:
{json.dumps(msg_dist, indent=2)}

TRILOGY SHARE OF VOICE:
{json.dumps(trilogy_share, indent=2)}

COMPETITOR A/B TESTS DETECTED:
{json.dumps(intel.get("ab_tests", [])[:3], indent=2, default=str)}

PROVEN TRILOGY HOOKS:
{json.dumps(BRAND["proven_hooks"])}

BRAND DIFFERENTIATORS:
{json.dumps(BRAND["differentiators"])}
"""

    prompt = f"""You are a senior media strategist at a top Australian ad agency. Your client is Trilogy Care.

Based on the competitive intelligence below, design {num_ads} new ad campaigns to run on Facebook, Instagram, and Google.

COMPETITIVE INTELLIGENCE:
{intel_summary[:3000]}

BRAND CONTEXT:
- Positioning: {BRAND["positioning"]}
- USP: {BRAND["usp"]}
- Target: {BRAND["audiences"]["primary"]["name"]} + {BRAND["audiences"]["secondary"]["name"]}
- Voice: {BRAND["voice"]["tone"]}
- Ambassador: {BRAND["ambassador"]}

AVAILABLE COPY FRAMEWORKS: {list(COPY_FRAMEWORKS.keys())}

For each ad, return:
{{
  "campaign_name": "short label",
  "objective": "awareness|consideration|conversion",
  "messaging_angle": "one of the 10 taxonomy angles",
  "target_audience": "primary|secondary|both",
  "platform": "facebook|instagram|google_search|google_display|youtube",
  "format": "static_image|video_15s|video_30s|carousel|stories",
  "copy_framework": "AIDA|PAS|BAB|4Ps",
  "hook_brief": "What the first 3 seconds / headline should convey",
  "key_message": "The single most important thing to communicate",
  "cta": "The call to action",
  "visual_direction": "What the image/video should show",
  "rationale": "Why this ad fills a gap or capitalizes on an opportunity",
  "priority": "high|medium|low"
}}

Return ONLY a valid JSON array of {num_ads} objects."""

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a media strategist. Return only valid JSON array."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=4000,
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3]
        return json.loads(text)
    except Exception as e:
        return [{"error": str(e)}]
