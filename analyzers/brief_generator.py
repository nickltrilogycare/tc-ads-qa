"""
Creative Brief Generator — generates Trilogy Care creative briefs inspired by competitor ads.
Uses Azure OpenAI GPT-4.1 to produce actionable briefs from high-performing competitor ads.
"""
import json
from openai import AzureOpenAI
from config import (
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_API_VERSION,
)


def get_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
    )


def generate_brief(
    inspiration_ad: dict,
    analysis: dict = None,
    trilogy_brand_context: str = None,
) -> dict:
    """
    Generate a Trilogy Care creative brief inspired by a competitor or high-performing ad.
    """
    client = get_client()
    analysis = analysis or {}

    brand_ctx = trilogy_brand_context or """
Trilogy Care is Australia's leading self-managed home care provider under the Support at Home program.
Brand values: Empowerment, independence, transparency, self-managed care.
Key differentiators: 26% flat low rate, no hidden fees, same day sign-on, choose your own workers.
Brand ambassador: Paula Duncan.
Tone: Warm, reassuring, empowering — not clinical or institutional.
Target audience: Older Australians (65+) and their adult children making care decisions.
Website: trilogycare.com.au | Phone: 1300 459 190
"""

    ad_text = json.dumps({
        "advertiser": inspiration_ad.get("advertiser", "Unknown"),
        "copy": inspiration_ad.get("copy_text") or inspiration_ad.get("full_text", ""),
        "format": inspiration_ad.get("ad_format", "unknown"),
        "cta": inspiration_ad.get("cta", ""),
        "score": analysis.get("overall_score", "N/A"),
        "strengths": analysis.get("strengths", []),
        "messaging_angles": analysis.get("messaging_angles", []),
    }, default=str)[:1500]

    prompt = f"""You are a senior creative strategist at an Australian aged care marketing agency.

Based on this competitor/reference ad, generate a creative brief for Trilogy Care to create a BETTER version.

## Reference Ad
{ad_text}

## Trilogy Care Brand Context
{brand_ctx}

## Output (JSON only)
{{
  "brief_title": "Short descriptive title for this brief",
  "objective": "What this ad should achieve",
  "target_audience": "Who we're talking to and what they care about",
  "key_message": "The single most important thing to communicate",
  "supporting_messages": ["2-3 supporting points"],
  "tone": "How the ad should feel",
  "format_recommendation": "video|static_image|carousel — with rationale",
  "headline_options": ["3 headline options"],
  "body_copy_draft": "A draft of the primary text (2-3 sentences)",
  "cta": "The call to action",
  "visual_direction": "What the creative should look like",
  "what_to_keep": "What works in the reference ad that we should replicate",
  "what_to_change": "What we should do differently for Trilogy's brand",
  "platform": "facebook|instagram|google_display|youtube"
}}"""

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a creative strategist. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=1500,
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3]
        return json.loads(text)
    except Exception as e:
        return {"error": str(e)}
