"""
Visual Brief Agent — creates Higgsfield-ready prompts for ad imagery/video.
Outputs detailed visual specs that can be fed into Higgsfield AI or any image gen tool.
"""
import json
from openai import AzureOpenAI
from config import (
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_API_VERSION,
)
from ad_creator.brand_context import BRAND


def get_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
    )


def generate_visual_brief(strategy_brief: dict, ad_copy: dict) -> dict:
    """
    Generate a Higgsfield-ready visual brief for an ad.
    Outputs detailed image/video prompts with brand guidelines.
    """
    client = get_client()
    fmt = strategy_brief.get("format", "static_image")
    platform = strategy_brief.get("platform", "facebook")

    prompt = f"""You are an art director creating visual briefs for aged care advertising in Australia.

Create a detailed visual brief for this ad that can be fed directly into Higgsfield AI (an AI image/video generation tool).

CAMPAIGN: {strategy_brief.get('campaign_name', '')}
PLATFORM: {platform}
FORMAT: {fmt}
HOOK: {ad_copy.get('hook', '') if isinstance(ad_copy, dict) else ''}
KEY MESSAGE: {strategy_brief.get('key_message', '')}
VISUAL DIRECTION: {strategy_brief.get('visual_direction', '')}
TARGET AUDIENCE: {strategy_brief.get('target_audience', '')}

BRAND COLORS: {json.dumps(BRAND['colors'])}
BRAND VOICE: {BRAND['voice']['tone']}
BRAND AMBASSADOR: {BRAND['ambassador']}

CRITICAL RULES FOR AGED CARE VISUALS:
- Show REAL, diverse older Australians (not stock photo models)
- Home environments (suburban Australian homes, gardens, living rooms)
- Active, engaged people — NOT passive or vulnerable
- Warm, natural lighting — NOT clinical/fluorescent
- Include family interactions where relevant
- Multicultural representation
- No hospital beds, wheelchairs as primary focus, or institutional settings

Return ONLY valid JSON:
{{
  "format": "{fmt}",
  "aspect_ratio": "1:1 for feed, 9:16 for stories, 16:9 for YouTube",
  "higgsfield_prompt": "Detailed prompt for Higgsfield AI image/video generation",
  "scene_description": "Detailed description of what the viewer sees",
  "color_palette": ["#hex1", "#hex2", "#hex3"],
  "text_overlay": {{
    "headline": "text to overlay on image",
    "position": "top|center|bottom",
    "font_style": "bold/regular, size suggestion"
  }},
  "mood_board_keywords": ["keyword1", "keyword2"],
  "lighting": "description of lighting",
  "setting": "description of the location/environment",
  "people": "who appears, what they're doing, what they're wearing",
  "props": "any objects or elements in the scene",
  {"\"storyboard\": [{\"scene\": 1, \"duration\": \"3s\", \"visual\": \"...\", \"audio\": \"...\", \"text_overlay\": \"...\"}]," if "video" in fmt else ""}
  "brand_elements": {{
    "logo_placement": "bottom-right corner",
    "color_usage": "how brand colors are incorporated",
    "cta_button": "visual design of the CTA"
  }},
  "do_not_include": ["list of things to avoid in the visual"]
}}"""

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are an art director. Return only valid JSON."},
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
        return {"error": str(e)}
