"""
Google Ads Transparency Center Scraper using Playwright.
Captures individual ad screenshots and images for visual dashboard.
"""
import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from config import SCREENSHOTS_DIR, DATA_DIR

AD_IMAGES_DIR = Path(__file__).parent.parent / "ad_images"


def scrape_google_ads(query: str, label: str = "", max_ads: int = 50) -> list[dict]:
    """
    Scrape ads from Google Ads Transparency Center.
    Captures individual ad screenshots for visual review.
    """
    label = label or query.replace(" ", "_")
    AD_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    url = "https://adstransparency.google.com/?hl=en"

    print(f"  [Google] Scraping ads for '{label}' ...")
    ads = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(3)

            # Accept cookies
            for selector in [
                'button:has-text("Accept all")',
                'button:has-text("Accept")',
                'button:has-text("I agree")',
            ]:
                try:
                    btn = page.query_selector(selector)
                    if btn and btn.is_visible():
                        btn.click()
                        time.sleep(1)
                except Exception:
                    pass

            # Search for the advertiser
            search_input = page.query_selector(
                'input[type="text"], input[type="search"], '
                'input[aria-label*="search" i], input[placeholder*="search" i], '
                'input[placeholder*="Find" i]'
            )
            if not search_input:
                search_areas = page.query_selector_all('[role="search"], [class*="search"]')
                for area in search_areas:
                    try:
                        area.click()
                        time.sleep(0.5)
                    except Exception:
                        pass
                search_input = page.query_selector('input[type="text"], input[type="search"], input')

            if search_input:
                search_input.click()
                time.sleep(0.5)
                search_input.fill(query)
                time.sleep(1)
                search_input.press("Enter")
                time.sleep(3)

            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(2)

            # Click first advertiser result
            advertiser_links = page.query_selector_all('a[href*="/advertiser/"]')
            if not advertiser_links:
                for sel in ['[role="listbox"] [role="option"]', '[class*="result"]']:
                    results = page.query_selector_all(sel)
                    if results:
                        results[0].click()
                        time.sleep(3)
                        break

            if advertiser_links:
                advertiser_links[0].click()
                time.sleep(3)
                try:
                    page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    pass

            # Scroll to load ads
            prev_height = 0
            for _ in range(min(max_ads // 5, 8)):
                page.evaluate("window.scrollBy(0, window.innerHeight)")
                time.sleep(1.5)
                curr_height = page.evaluate("document.body.scrollHeight")
                if curr_height == prev_height:
                    break
                prev_height = curr_height

            # Extract ad cards with element screenshots
            ad_selectors = [
                "creative-preview",
                '[class*="ad-card"]',
                '[class*="creative-card"]',
                "material-card",
                '[role="listitem"]',
            ]

            ad_elements = []
            for sel in ad_selectors:
                ad_elements = page.query_selector_all(sel)
                if len(ad_elements) >= 1:
                    break

            current_url = page.url

            if ad_elements:
                for i, el in enumerate(ad_elements[:max_ads]):
                    try:
                        text = el.inner_text().strip()

                        # Take element screenshot
                        el_ss_path = AD_IMAGES_DIR / f"google_{label}_ad{i}_{datetime.now():%Y%m%d}.png"
                        try:
                            el.screenshot(path=str(el_ss_path))
                        except Exception:
                            el_ss_path = None

                        # Get images within this ad
                        images = el.query_selector_all("img")
                        image_paths = []
                        image_urls = []
                        for j, img in enumerate(images[:2]):
                            src = img.get_attribute("src") or ""
                            if src and len(src) > 20:
                                image_urls.append(src)
                                # Download image
                                img_filename = f"google_{label}_ad{i}_img{j}_{datetime.now():%Y%m%d}.png"
                                img_path = AD_IMAGES_DIR / img_filename
                                if not img_path.exists():
                                    try:
                                        urllib.request.urlretrieve(src, str(img_path))
                                        image_paths.append(str(img_path))
                                    except Exception:
                                        image_paths.append(src)
                                else:
                                    image_paths.append(str(img_path))

                        # Detect format
                        has_video = bool(el.query_selector("video"))
                        has_image = bool(images)
                        ad_format = "video" if has_video else "image" if has_image else "text"

                        # Check for format icon text
                        if "videocam" in text.lower():
                            ad_format = "video"

                        ad_data = {
                            "source": "google",
                            "advertiser": label,
                            "ad_index": i,
                            "ad_url": current_url,
                            "full_text": text[:2000],
                            "copy_text": text.replace("videocam", "").replace(label, "").strip()[:500],
                            "ad_format": ad_format,
                            "has_video": has_video,
                            "has_image": has_image,
                            "image_paths": image_paths,
                            "image_urls": image_urls,
                            "element_screenshot": str(el_ss_path) if el_ss_path else None,
                            "scraped_at": datetime.now().isoformat(),
                        }
                        ads.append(ad_data)
                    except Exception as e:
                        print(f"  [Google] Error parsing ad {i}: {e}")
            else:
                # Fallback
                body_text = page.inner_text("body")
                ads.append({
                    "source": "google",
                    "advertiser": label,
                    "raw_text": body_text[:5000],
                    "extraction_method": "full_page_text",
                    "ad_format": "unknown",
                    "image_paths": [],
                    "image_urls": [],
                    "scraped_at": datetime.now().isoformat(),
                    "ad_url": current_url,
                })

            # Full page screenshot
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(0.5)
            ss_path = SCREENSHOTS_DIR / f"google_{label}_{datetime.now():%Y%m%d_%H%M}.png"
            page.screenshot(path=str(ss_path), full_page=True)

            print(f"  [Google] Found {len(ads)} ads for '{label}'")

        except PWTimeout:
            print(f"  [Google] Timeout loading page for '{label}'")
        except Exception as e:
            print(f"  [Google] Error scraping '{label}': {e}")
        finally:
            browser.close()

    # Save raw data
    out_path = DATA_DIR / f"google_{label}_{datetime.now():%Y%m%d}.json"
    with open(out_path, "w") as f:
        json.dump(ads, f, indent=2, default=str)

    return ads
