"""
Trilogy Care Brand Context — Single source of truth for all ad creation agents.
"""

BRAND = {
    "name": "Trilogy Care",
    "tagline": "The care to keep you home",
    "website": "trilogycare.com.au",
    "phone": "1300 459 190",
    "ambassador": "Paula Duncan",

    # Brand positioning
    "positioning": "Australia's leading self-managed home care provider under Support at Home",
    "usp": "26% flat management fee — no hidden fees, no exit fees. More of your funding goes to actual care.",
    "model": "Self-managed home care — you choose your own workers, set your own schedule, control your own budget",

    # Key differentiators
    "differentiators": [
        "26% flat low rate (vs industry avg 35-45%)",
        "100% no hidden or exit fees",
        "Same day sign-on — start care immediately",
        "Choose your own workers",
        "Self-managed with support — not left alone",
        "Transparent fee structure visible online",
        "10% care management cap under Support at Home",
        "Paula Duncan as brand ambassador",
    ],

    # Brand colors
    "colors": {
        "primary_blue": "#1B3A5C",
        "accent_teal": "#00A5B5",
        "warm_orange": "#F58220",
        "heart_red": "#E4002B",
        "cream": "#FFF8F0",
        "white": "#FFFFFF",
    },

    # Brand voice
    "voice": {
        "tone": "Warm, reassuring, empowering — never clinical or institutional",
        "personality": "Like a trusted friend who happens to be an expert in aged care",
        "do": [
            "Speak directly to the reader (you, your)",
            "Use plain English — no jargon",
            "Lead with empathy, follow with facts",
            "Highlight independence and choice",
            "Be transparent about costs",
            "Use real stories and testimonials",
        ],
        "dont": [
            "Sound corporate or bureaucratic",
            "Use clinical language (patient, facility, placement)",
            "Make fear-based appeals",
            "Be patronizing about age",
            "Hide fees or costs",
            "Use stock photos of generic elderly people",
        ],
    },

    # Target audiences
    "audiences": {
        "primary": {
            "name": "Older Australians (65+)",
            "description": "People approved for or receiving Support at Home funding",
            "pain_points": [
                "Confused by the new Support at Home system",
                "Worried about losing independence",
                "Frustrated by provider fees eating into their funding",
                "Want to choose their own carers",
                "Don't want to leave their home",
            ],
            "motivations": [
                "Stay independent at home",
                "Get more care hours from their funding",
                "Have control over their care",
                "Feel safe and supported",
            ],
        },
        "secondary": {
            "name": "Adult children (35-60)",
            "description": "Sons and daughters helping parents navigate aged care",
            "pain_points": [
                "Overwhelmed by the aged care system",
                "Worried about parent's safety at home",
                "Want transparency on what they're paying for",
                "Don't trust providers to do the right thing",
                "Feeling guilty about not doing enough",
            ],
            "motivations": [
                "Peace of mind that Mum/Dad is safe",
                "Easy to understand and manage",
                "Good value — funding goes to care, not admin",
                "A provider they can trust",
            ],
        },
    },

    # Ad copy patterns that work
    "proven_hooks": [
        "More hours. Same funding.",
        "Home is where you belong.",
        "If you've been approved for home care...",
        "Same service, double the price?",
        "Confused about Support at Home?",
        "Your guide to making every care hour matter",
        "Choose the care that keeps you where you belong",
    ],

    # Compliance requirements
    "compliance": {
        "regulator": "Aged Care Quality and Safety Commission (ACQSC)",
        "rules": [
            "No misleading claims about service quality",
            "Transparent pricing must be verifiable",
            "Appropriate representation of older Australians",
            "Cannot guarantee specific care outcomes",
            "Must not exploit vulnerability or create undue fear",
            "Claims about savings must be substantiated",
        ],
    },

    # Platform specs
    "platform_specs": {
        "facebook": {
            "primary_text": {"max_chars": 125, "recommended": "Short, punchy — front-load the hook"},
            "headline": {"max_chars": 40, "recommended": "Clear value proposition"},
            "description": {"max_chars": 30},
            "image": {"ratio": "1:1 or 4:5", "min_size": "1080x1080"},
            "video": {"max_length": "15-30s", "recommended": "6-15s for feed, 15-30s for stories"},
            "ctas": ["Learn More", "Sign Up", "Get Quote", "Contact Us", "Book Now"],
        },
        "instagram": {
            "primary_text": {"max_chars": 125},
            "headline": {"max_chars": 40},
            "image": {"ratio": "1:1 or 9:16 (stories)", "min_size": "1080x1080"},
            "video": {"max_length": "60s feed, 15s stories"},
        },
        "google_search": {
            "headlines": {"max_chars": 30, "count": "up to 15"},
            "descriptions": {"max_chars": 90, "count": "up to 4"},
            "sitelinks": True,
        },
        "google_display": {
            "headlines": {"max_chars": 30, "short": True},
            "description": {"max_chars": 90},
            "images": {"sizes": ["1200x628", "1200x1200", "300x250"]},
        },
        "youtube": {
            "video": {"recommended": "15-30s pre-roll, 6s bumper"},
            "companion_banner": "300x60",
        },
    },
}


# Ad copy frameworks
COPY_FRAMEWORKS = {
    "AIDA": {
        "name": "Attention-Interest-Desire-Action",
        "structure": [
            "Attention: Hook that stops the scroll",
            "Interest: Problem or insight they relate to",
            "Desire: Show the solution and what life looks like",
            "Action: Clear CTA",
        ],
        "best_for": "Facebook feed ads, Google Display",
    },
    "PAS": {
        "name": "Problem-Agitate-Solution",
        "structure": [
            "Problem: Name the pain point",
            "Agitate: Make them feel it — what happens if nothing changes",
            "Solution: Trilogy Care fixes this",
        ],
        "best_for": "Emotional video ads, Instagram stories",
    },
    "BAB": {
        "name": "Before-After-Bridge",
        "structure": [
            "Before: Life now (struggling with aged care system)",
            "After: Life with Trilogy Care (independent, in control)",
            "Bridge: How to get there (call/visit/sign up)",
        ],
        "best_for": "Testimonial ads, comparison ads",
    },
    "4Ps": {
        "name": "Promise-Picture-Proof-Push",
        "structure": [
            "Promise: Lead with the benefit",
            "Picture: Paint the outcome",
            "Proof: Credential or social proof",
            "Push: CTA with urgency",
        ],
        "best_for": "Google Search ads, retargeting",
    },
}
