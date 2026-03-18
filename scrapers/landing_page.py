"""
Landing Page Scraper — captures screenshots and metadata from ad destination URLs.
Follows CTA links from ads and captures the landing page experience.
"""
import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

LP_DIR = Path(__file__).parent.parent / "landing_pages"
LP_DIR.mkdir(exist_ok=True)


def capture_landing_page(url: str, label: str = "") -> dict:
    """
    Navigate to an ad's landing page and capture screenshot + metadata.
    Returns dict with screenshot path, headline, form fields, etc.
    """
    result = {
        "url": url,
        "label": label,
        "screenshot": None,
        "title": "",
        "headline": "",
        "has_form": False,
        "form_fields": [],
        "has_phone": False,
        "phone_number": "",
        "meta_description": "",
        "captured_at": datetime.now().isoformat(),
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        try:
            page.goto(url, wait_until="networkidle", timeout=20000)
            time.sleep(2)

            # Close cookie banners
            for sel in ['button:has-text("Accept")', 'button:has-text("Close")', '[aria-label="Close"]']:
                try:
                    btn = page.query_selector(sel)
                    if btn and btn.is_visible():
                        btn.click()
                        time.sleep(0.5)
                except Exception:
                    pass

            # Screenshot
            ss_path = LP_DIR / f"lp_{label}_{datetime.now():%Y%m%d_%H%M}.png"
            page.screenshot(path=str(ss_path), full_page=False)
            result["screenshot"] = str(ss_path)

            # Extract metadata
            result["title"] = page.title() or ""

            # Get meta description
            meta = page.query_selector('meta[name="description"]')
            if meta:
                result["meta_description"] = meta.get_attribute("content") or ""

            # Find headline (h1)
            h1 = page.query_selector("h1")
            if h1:
                result["headline"] = h1.inner_text().strip()[:200]

            # Check for forms
            forms = page.query_selector_all("form")
            if forms:
                result["has_form"] = True
                for form in forms[:2]:
                    inputs = form.query_selector_all("input, select, textarea")
                    for inp in inputs:
                        input_type = inp.get_attribute("type") or "text"
                        name = inp.get_attribute("name") or inp.get_attribute("placeholder") or ""
                        if input_type not in ("hidden", "submit"):
                            result["form_fields"].append(f"{input_type}: {name}")

            # Check for phone numbers
            body_text = page.inner_text("body")
            import re
            phone_match = re.search(r"1[38]00[\s-]?\d{3}[\s-]?\d{3}", body_text)
            if phone_match:
                result["has_phone"] = True
                result["phone_number"] = phone_match.group()

        except Exception as e:
            result["error"] = str(e)
        finally:
            browser.close()

    return result


def batch_capture(ads: list[dict], max_pages: int = 10) -> list[dict]:
    """Capture landing pages for ads that have identifiable URLs."""
    results = []
    seen_urls = set()

    for ad in ads:
        # Try to extract URL from ad copy
        text = ad.get("copy_text") or ad.get("full_text", "")
        import re
        urls = re.findall(r'https?://[^\s<>"]+|(?:trilogycare|boltonclarke|hammondcare|dovida)\.\w+\.\w+[^\s<>"]*', text)

        for url in urls[:1]:
            if not url.startswith("http"):
                url = "https://" + url
            if url in seen_urls:
                continue
            seen_urls.add(url)

            label = ad.get("advertiser", "unknown")
            print(f"  [LP] Capturing {label}: {url[:60]}...")
            result = capture_landing_page(url, label)
            result["advertiser"] = label
            results.append(result)

            if len(results) >= max_pages:
                return results

    return results
