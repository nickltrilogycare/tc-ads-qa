"""
Ad Quality Analyzer — uses Azure OpenAI GPT-4.1 to score and critique ads.
"""
import json
from openai import AzureOpenAI
from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION,
    QUALITY_THRESHOLDS,
    SCORING_WEIGHTS,
)


def get_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
    )


QUALITY_PROMPT = """You are an expert digital advertising QA analyst specialising in Australian aged care / home care advertising.

Analyse the following ad data and provide a structured quality assessment.

## Scoring Categories (100 points total)
1. **Copy Quality** ({copy_quality} pts): Clarity, persuasion, emotional resonance, grammar, CTA strength. For aged care: empathy, dignity, trust signals.
2. **Visual Quality** ({visual_quality} pts): Design professionalism, brand alignment, image relevance. Note if we only have text (score based on what's available).
3. **Targeting Signals** ({targeting_signals} pts): Audience relevance — does the ad speak to the right audience (older Australians, adult children, carers)?
4. **Compliance** ({compliance} pts): Aged care advertising regulations (no misleading claims, appropriate imagery of older people, ACQSC alignment).
5. **Brand Consistency** ({brand_consistency} pts): Alignment with brand voice and positioning. For Trilogy Care: self-managed, empowerment, independence, transparent fees.
6. **Freshness** ({freshness} pts): Appears current and timely vs stale/outdated.

## Ad Data
```
{ad_data}
```

## Advertiser
{advertiser}

## Output Format (JSON)
Return ONLY valid JSON:
{{
  "overall_score": <0-100>,
  "category_scores": {{
    "copy_quality": {{"score": <0-{copy_quality}>, "notes": "..."}},
    "visual_quality": {{"score": <0-{visual_quality}>, "notes": "..."}},
    "targeting_signals": {{"score": <0-{targeting_signals}>, "notes": "..."}},
    "compliance": {{"score": <0-{compliance}>, "notes": "..."}},
    "brand_consistency": {{"score": <0-{brand_consistency}>, "notes": "..."}},
    "freshness": {{"score": <0-{freshness}>, "notes": "..."}}
  }},
  "ad_type": "image|video|text|carousel|unknown",
  "copy_text_extracted": "the main ad copy if identifiable",
  "cta_identified": "the CTA if present",
  "issues": [
    {{"severity": "critical|high|medium|low", "issue": "description", "recommendation": "fix"}}
  ],
  "strengths": ["list of things done well"],
  "competitor_relevance": "how this compares to typical aged care advertising"
}}
"""


def analyze_ad(ad: dict) -> dict:
    """Score a single ad using GPT-4.1."""
    client = get_client()

    ad_text = json.dumps(ad, indent=2, default=str)[:3000]

    prompt = QUALITY_PROMPT.format(
        ad_data=ad_text,
        advertiser=ad.get("advertiser", "Unknown"),
        **SCORING_WEIGHTS,
    )

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are an advertising quality analyst. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
        )

        result_text = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if result_text.startswith("```"):
            result_text = result_text.split("\n", 1)[1]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

        result = json.loads(result_text)
        result["source_ad"] = {
            "advertiser": ad.get("advertiser"),
            "source": ad.get("source"),
            "ad_index": ad.get("ad_index"),
        }
        return result

    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to parse AI response: {e}",
            "raw_response": result_text[:500] if "result_text" in dir() else "no response",
            "source_ad": ad.get("advertiser", "Unknown"),
        }
    except Exception as e:
        return {
            "error": str(e),
            "source_ad": ad.get("advertiser", "Unknown"),
        }


def analyze_all_ads(ads: list[dict]) -> list[dict]:
    """Analyze a batch of ads, returning scored results."""
    results = []
    for i, ad in enumerate(ads):
        print(f"    Analyzing ad {i+1}/{len(ads)} ({ad.get('advertiser', '?')})...")
        result = analyze_ad(ad)
        results.append(result)
    return results


def flag_poor_quality(results: list[dict], threshold: int = 50) -> list[dict]:
    """Return ads scoring below the threshold."""
    poor = []
    for r in results:
        score = r.get("overall_score", 0)
        if score < threshold:
            poor.append(r)
    return sorted(poor, key=lambda x: x.get("overall_score", 0))
