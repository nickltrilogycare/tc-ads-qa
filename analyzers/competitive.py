"""
Competitive Ad Analysis — compares Trilogy ads vs competitor ads.
"""
import json
from openai import AzureOpenAI
from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION,
)


def get_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
    )


COMPETITIVE_PROMPT = """You are an expert competitive intelligence analyst specialising in Australian aged care advertising.

Compare Trilogy Care's advertising against their competitors based on the data below.

## Trilogy Care Ads
```
{trilogy_ads}
```

## Competitor Ads
```
{competitor_ads}
```

## Analysis Required
Provide a structured competitive analysis covering:

1. **Messaging Comparison**: What themes/messages is each advertiser using? Who has stronger value propositions?
2. **Creative Approach**: Visual styles, formats used (video vs static vs carousel), production quality differences.
3. **CTA Strategy**: What actions are advertisers driving? Which CTAs are likely most effective?
4. **Audience Targeting Signals**: Who seems to be the target audience for each? Any gaps Trilogy is missing?
5. **Differentiation**: What makes Trilogy stand out (or not) vs competitors?
6. **Ad Volume & Freshness**: Who is running more ads? Who refreshes creative more often?
7. **Regulatory Compliance**: Any competitors making claims Trilogy should be wary of, or best practices to adopt?

## Output Format (JSON)
Return ONLY valid JSON:
{{
  "executive_summary": "2-3 sentence overview for the CMO",
  "trilogy_strengths": ["things Trilogy does better"],
  "trilogy_weaknesses": ["gaps vs competitors"],
  "competitor_highlights": {{
    "competitor_name": {{
      "notable_ads": "what stands out",
      "threats": "what Trilogy should worry about",
      "opportunities": "what Trilogy could learn/adopt"
    }}
  }},
  "recommendations": [
    {{"priority": "high|medium|low", "action": "specific recommendation", "rationale": "why"}}
  ],
  "market_trends": ["observed trends across all advertisers"],
  "ad_volume_comparison": {{
    "Trilogy Care": {{"estimated_active_ads": "number or range", "platforms": ["fb", "google"]}},
    "competitor_name": {{"estimated_active_ads": "number or range", "platforms": ["fb", "google"]}}
  }}
}}
"""


def run_competitive_analysis(
    trilogy_ads: list[dict],
    competitor_ads: dict[str, list[dict]],
) -> dict:
    """
    Compare Trilogy's ads against all competitors.
    competitor_ads: {"Competitor Name": [ad_dicts]}
    """
    client = get_client()

    # Summarise ads to fit context
    def summarise(ads: list[dict], max_chars=2000) -> str:
        summaries = []
        for ad in ads[:10]:
            text = ad.get("full_text") or ad.get("raw_text", "")
            summaries.append(json.dumps({
                "text": text[:300],
                "source": ad.get("source"),
                "has_video": ad.get("has_video"),
                "has_image": ad.get("has_image"),
                "cta": ad.get("cta_texts", []),
                "format": ad.get("format", "unknown"),
            }, default=str))
        return "\n".join(summaries)[:max_chars]

    trilogy_summary = summarise(trilogy_ads)

    comp_summary_parts = []
    for name, ads in competitor_ads.items():
        comp_summary_parts.append(f"### {name}\n{summarise(ads, 1000)}")
    comp_summary = "\n\n".join(comp_summary_parts)[:4000]

    prompt = COMPETITIVE_PROMPT.format(
        trilogy_ads=trilogy_summary,
        competitor_ads=comp_summary,
    )

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a competitive intelligence analyst. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=3000,
        )

        result_text = response.choices[0].message.content.strip()
        if result_text.startswith("```"):
            result_text = result_text.split("\n", 1)[1]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

        return json.loads(result_text)

    except Exception as e:
        return {"error": str(e)}
