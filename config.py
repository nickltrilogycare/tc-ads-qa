"""
TC Ads QA Tool — Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load env from tc-chiefs
load_dotenv(Path(__file__).parent.parent / "tc-chiefs" / ".env")

# --- Azure OpenAI (for ad analysis) ---
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "trilogy-gpt-4.1")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")

# --- Paths ---
PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data"
SCREENSHOTS_DIR = PROJECT_DIR / "screenshots"
REPORTS_DIR = PROJECT_DIR / "reports"

# --- Trilogy Care ---
TRILOGY_FACEBOOK_PAGE_ID = "trilogycare"
TRILOGY_GOOGLE_ADVERTISER_QUERY = "Trilogy Care"
TRILOGY_WEBSITE = "trilogycare.com.au"

# --- Competitors ---
COMPETITORS = {
    "HomeMade": {
        "facebook_page": "homemadehomecare",
        "google_query": "HomeMade home care",
        "website": "homemade.com.au",
    },
    "Bolton Clarke": {
        "facebook_page": "BoltonClarke",
        "google_query": "Bolton Clarke",
        "website": "boltonclarke.com.au",
    },
    "HammondCare": {
        "facebook_page": "HammondCare",
        "google_query": "HammondCare",
        "website": "hammondcare.com.au",
    },
    "Just Better Care": {
        "facebook_page": "JustBetterCare",
        "google_query": "Just Better Care",
        "website": "justbettercare.com",
    },
    "Dovida (Home Instead)": {
        "facebook_page": "DovidaAustralia",
        "google_query": "Dovida home care",
        "website": "dovida.com.au",
    },
    "KinCare (Silverchain)": {
        "facebook_page": "KinCare",
        "google_query": "KinCare",
        "website": "kincare.com.au",
    },
}

# --- Ad Quality Thresholds ---
QUALITY_THRESHOLDS = {
    "min_copy_length": 30,          # chars — too short = low effort
    "max_copy_length": 1000,        # chars — too long = wall of text
    "min_cta_score": 1,             # must have at least 1 clear CTA
    "max_text_on_image_pct": 20,    # Meta's old 20% text rule (still best practice)
    "min_relevance_score": 6,       # out of 10
    "freshness_days": 90,           # flag ads older than this
}

# --- Quality Scoring Weights ---
SCORING_WEIGHTS = {
    "copy_quality": 25,       # clarity, persuasion, CTA strength
    "visual_quality": 20,     # design, branding, image quality
    "targeting_signals": 15,  # audience relevance indicators
    "compliance": 15,         # regulatory (aged care specific)
    "brand_consistency": 15,  # alignment with Trilogy brand
    "freshness": 10,          # how recently updated
}
