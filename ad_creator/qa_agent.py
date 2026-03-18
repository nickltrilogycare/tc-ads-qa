"""
QA Agent — reviews all ad components for quality, compliance, and brand consistency.
Acts as the final gate before any ad goes to production.
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


def qa_review(
    strategy_brief: dict,
    hooks: list[dict],
    ad_copy: list[dict],
    visual_brief: dict,
) -> dict:
    """
    Comprehensive QA review of all ad components.
    Checks: compliance, brand voice, copy quality, visual appropriateness, platform fit.
    Returns pass/fail with detailed feedback.
    """
    client = get_client()

    prompt = f"""You are a senior advertising compliance and quality reviewer specializing in Australian aged care.

Review this ad package for Trilogy Care and provide a detailed QA assessment.

STRATEGY BRIEF:
{json.dumps(strategy_brief, indent=2, default=str)[:800]}

HOOKS (top 3):
{json.dumps(hooks[:3], indent=2, default=str)[:600]}

AD COPY:
{json.dumps(ad_copy[:2], indent=2, default=str)[:1000]}

VISUAL BRIEF:
{json.dumps(visual_brief, indent=2, default=str)[:800]}

REVIEW AGAINST:

1. COMPLIANCE (Aged Care Quality and Safety Commission):
{json.dumps(BRAND['compliance']['rules'])}

2. BRAND VOICE:
   Tone: {BRAND['voice']['tone']}
   DO: {json.dumps(BRAND['voice']['do'])}
   DON'T: {json.dumps(BRAND['voice']['dont'])}

3. PLATFORM SPECS:
   Are character limits respected? Is the format appropriate for the platform?

4. COPY QUALITY:
   Grammar, clarity, persuasiveness, CTA strength, emotional resonance

5. VISUAL APPROPRIATENESS:
   Does the visual direction respect aged care representation guidelines?

Return ONLY valid JSON:
{{
  "overall_verdict": "APPROVED|NEEDS_REVISION|REJECTED",
  "overall_score": 0-100,
  "compliance_check": {{
    "passed": true/false,
    "issues": ["list of compliance issues if any"],
    "severity": "none|minor|major|critical"
  }},
  "brand_voice_check": {{
    "passed": true/false,
    "issues": ["list of brand voice issues"],
    "tone_alignment": 0-10
  }},
  "copy_quality_check": {{
    "passed": true/false,
    "issues": ["list of copy issues"],
    "hook_strength": 0-10,
    "cta_strength": 0-10,
    "clarity": 0-10
  }},
  "visual_check": {{
    "passed": true/false,
    "issues": ["list of visual concerns"],
    "appropriateness": 0-10
  }},
  "platform_fit_check": {{
    "passed": true/false,
    "issues": ["character limit violations, format issues"],
  }},
  "revision_suggestions": [
    {{"component": "hook|copy|visual|strategy", "suggestion": "specific fix", "priority": "high|medium|low"}}
  ],
  "strongest_element": "what's best about this ad package",
  "weakest_element": "what needs the most work"
}}"""

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a compliance reviewer. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=2000,
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3]
        return json.loads(text)
    except Exception as e:
        return {"error": str(e), "overall_verdict": "ERROR"}
