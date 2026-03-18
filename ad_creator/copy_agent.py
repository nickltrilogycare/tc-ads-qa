"""
Copy Agent — writes full ad copy using proven frameworks.
Takes a strategy brief + selected hook and produces complete ad copy for each platform.
"""
import json
from openai import AzureOpenAI
from config import (
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_API_VERSION,
)
from ad_creator.brand_context import BRAND, COPY_FRAMEWORKS


def get_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
    )


def generate_ad_copy(strategy_brief: dict, hook: dict) -> dict:
    """
    Generate complete ad copy for a specific platform using the selected hook.
    Returns platform-ready copy with all required fields.
    """
    client = get_client()
    platform = strategy_brief.get("platform", "facebook")
    framework = strategy_brief.get("copy_framework", "AIDA")
    specs = BRAND["platform_specs"].get(platform, BRAND["platform_specs"]["facebook"])
    framework_detail = COPY_FRAMEWORKS.get(framework, COPY_FRAMEWORKS["AIDA"])

    prompt = f"""You are an expert social media ad copywriter for Australian aged care.

Write complete ad copy for this campaign, following the {framework} framework.

CAMPAIGN:
- Name: {strategy_brief.get('campaign_name', '')}
- Platform: {platform}
- Format: {strategy_brief.get('format', '')}
- Objective: {strategy_brief.get('objective', '')}
- Target: {strategy_brief.get('target_audience', '')}
- Key message: {strategy_brief.get('key_message', '')}
- CTA: {strategy_brief.get('cta', '')}

SELECTED HOOK: "{hook.get('hook_text', '')}"

COPY FRAMEWORK ({framework}):
{json.dumps(framework_detail['structure'])}

BRAND VOICE: {BRAND['voice']['tone']}
DO: {json.dumps(BRAND['voice']['do'])}
DON'T: {json.dumps(BRAND['voice']['dont'])}

PLATFORM SPECS:
{json.dumps(specs, indent=2)}

BRAND DETAILS:
- Name: {BRAND['name']}
- USP: {BRAND['usp']}
- Phone: {BRAND['phone']}
- Website: {BRAND['website']}

Write the ad copy. Return ONLY valid JSON:
{{
  "platform": "{platform}",
  "hook": "{hook.get('hook_text', '')}",
  "primary_text": "The main ad copy (respect character limits)",
  "headline": "The headline (max {specs.get('headline', {}).get('max_chars', 40)} chars)",
  "description": "Description line if applicable",
  "cta_button": "The CTA button text",
  "hashtags": ["relevant hashtags if social"],
  "url": "trilogycare.com.au/relevant-landing-page",
  "copy_framework_used": "{framework}",
  "ab_variant": "A",
  "word_count": 0,
  "character_count": 0
}}

ALSO generate a B variant with a different angle on the same message:
Return a JSON array with [variant_A, variant_B]"""

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are an ad copywriter. Return only valid JSON array."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=2000,
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3]
        return json.loads(text)
    except Exception as e:
        return [{"error": str(e)}]


def generate_google_search_copy(strategy_brief: dict) -> dict:
    """Generate Google Search responsive ad copy (multiple headlines + descriptions)."""
    client = get_client()

    prompt = f"""Write Google Responsive Search Ad copy for Trilogy Care.

CAMPAIGN: {strategy_brief.get('campaign_name', '')}
KEY MESSAGE: {strategy_brief.get('key_message', '')}

BRAND: {BRAND['name']} | {BRAND['usp']}
PHONE: {BRAND['phone']}
WEBSITE: {BRAND['website']}

Generate:
- 15 headlines (max 30 chars each) — mix of benefit, feature, CTA, brand, and keyword headlines
- 4 descriptions (max 90 chars each) — compelling value props with CTAs

Return ONLY valid JSON:
{{
  "headlines": ["headline1", "headline2", ...],
  "descriptions": ["desc1", "desc2", ...],
  "final_url": "https://trilogycare.com.au/relevant-page",
  "display_url_path": ["support-at-home", "self-managed"],
  "sitelinks": [
    {{"headline": "...", "description": "...", "url": "..."}},
  ]
}}"""

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a Google Ads specialist. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=2000,
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3]
        return json.loads(text)
    except Exception as e:
        return {"error": str(e)}
