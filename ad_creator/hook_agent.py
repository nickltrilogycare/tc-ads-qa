"""
Hook Agent — specializes in creating attention-grabbing hooks.
The first 3 seconds of video / first line of copy determines whether anyone reads the rest.
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


HOOK_TYPES = {
    "question": "Ask a question the audience can't ignore",
    "stat_shock": "Lead with a surprising statistic",
    "story_open": "Start a mini-story ('When Mum was told she needed care...')",
    "direct_address": "Speak directly to their situation ('If you've been approved for home care...')",
    "comparison": "Compare two scenarios ('Same service, double the price?')",
    "social_proof": "Lead with a testimonial or number ('Join 5,000+ Australians who...')",
    "fear_reversal": "Name the fear, then immediately flip it ('You don't have to leave your home.')",
    "curiosity_gap": "Tease information they need ('The hidden fee most home care providers don't tell you about')",
}


def generate_hooks(strategy_brief: dict, num_hooks: int = 5) -> list[dict]:
    """
    Generate multiple hook options for a single ad brief.
    Each hook is tested against different hook types.
    """
    client = get_client()

    prompt = f"""You are a world-class direct response copywriter specializing in aged care advertising in Australia.

Generate {num_hooks} different hooks for this ad campaign. Each hook must stop the scroll in under 3 seconds.

CAMPAIGN BRIEF:
- Campaign: {strategy_brief.get('campaign_name', '')}
- Messaging angle: {strategy_brief.get('messaging_angle', '')}
- Target: {strategy_brief.get('target_audience', '')}
- Platform: {strategy_brief.get('platform', '')}
- Format: {strategy_brief.get('format', '')}
- Key message: {strategy_brief.get('key_message', '')}
- Hook direction: {strategy_brief.get('hook_brief', '')}

HOOK TYPES TO USE (pick different ones for variety):
{json.dumps(HOOK_TYPES, indent=2)}

BRAND VOICE: {BRAND['voice']['tone']}
PROVEN HOOKS THAT WORK: {json.dumps(BRAND['proven_hooks'])}

AUDIENCE PAIN POINTS:
- Primary (65+): {json.dumps(BRAND['audiences']['primary']['pain_points'])}
- Secondary (35-60): {json.dumps(BRAND['audiences']['secondary']['pain_points'])}

For each hook, return:
{{
  "hook_text": "The exact hook text (1-2 sentences max)",
  "hook_type": "question|stat_shock|story_open|direct_address|comparison|social_proof|fear_reversal|curiosity_gap",
  "target": "primary|secondary",
  "platform_fit": "why this hook works on the target platform",
  "video_visual": "what's on screen during this hook (for video ads)",
  "estimated_strength": 1-10
}}

Return ONLY a valid JSON array."""

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a direct response copywriter. Return only valid JSON array."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
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
