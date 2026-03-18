"""
Competitor Strategy Analyzer — deep comparison of each competitor's ad strategy vs Trilogy Care.
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


def analyze_competitor_strategy(
    trilogy_ads: list[dict],
    competitor_name: str,
    competitor_ads: list[dict],
) -> dict:
    """Produce a deep strategic comparison of one competitor vs Trilogy Care."""
    client = get_client()

    def summarise(ads, max_chars=2500):
        parts = []
        for ad in ads[:15]:
            text = ad.get("copy_text") or ad.get("full_text", "")
            parts.append(json.dumps({
                "copy": text[:300],
                "format": ad.get("ad_format", "unknown"),
                "cta": ad.get("cta", ""),
                "date": ad.get("start_date", ""),
                "source": ad.get("source", ""),
            }, default=str))
        return "\n".join(parts)[:max_chars]

    prompt = f"""You are a senior media strategist at an Australian aged care marketing agency.

Compare {competitor_name}'s Support at Home advertising strategy against Trilogy Care's.

## Trilogy Care Ads
{summarise(trilogy_ads)}

## {competitor_name} Ads
{summarise(competitor_ads)}

Produce a deep strategic analysis. Return ONLY valid JSON:
{{
  "competitor": "{competitor_name}",
  "summary": "2-3 sentence strategic overview",
  "messaging_strategy": {{
    "competitor_themes": ["their key messages"],
    "trilogy_themes": ["our key messages"],
    "differentiation": "what makes each unique",
    "overlap": "where messaging is similar"
  }},
  "creative_strategy": {{
    "competitor_formats": {{"video_pct": 0, "image_pct": 0, "text_pct": 0}},
    "trilogy_formats": {{"video_pct": 0, "image_pct": 0, "text_pct": 0}},
    "production_quality_comparison": "who has better creative quality and why",
    "creative_volume": "who is running more ads"
  }},
  "audience_strategy": {{
    "competitor_target": "who they seem to be targeting",
    "trilogy_target": "who we seem to be targeting",
    "gaps": "audience segments one is reaching that the other isn't"
  }},
  "cta_strategy": {{
    "competitor_ctas": ["list of CTAs used"],
    "trilogy_ctas": ["list of CTAs used"],
    "effectiveness_comparison": "whose CTAs are likely more effective"
  }},
  "threat_level": "low|medium|high",
  "threat_rationale": "why this competitor is or isn't a threat",
  "actions_for_trilogy": [
    {{"priority": "high|medium|low", "action": "specific thing Trilogy should do", "rationale": "why"}}
  ]
}}"""

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a media strategist. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3]
        return json.loads(text)
    except Exception as e:
        return {"error": str(e), "competitor": competitor_name}


def analyze_all_competitors(
    trilogy_ads: list[dict],
    competitor_ads: dict[str, list[dict]],
) -> dict[str, dict]:
    """Run strategy analysis for each competitor."""
    results = {}
    for name, ads in competitor_ads.items():
        if ads:
            print(f"  Analyzing strategy: {name} vs Trilogy Care...")
            results[name] = analyze_competitor_strategy(trilogy_ads, name, ads)
    return results
