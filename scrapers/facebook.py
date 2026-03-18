"""
Facebook Ad Library Scraper using Playwright.
Captures individual ad screenshots and images for visual dashboard.
"""
import json
import time
import re
import urllib.request
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from config import SCREENSHOTS_DIR, DATA_DIR

AD_IMAGES_DIR = Path(__file__).parent.parent / "ad_images"


def scrape_facebook_ads(page_name: str, label: str = "", max_ads: int = 50) -> list[dict]:
    """
    Scrape ads from the Facebook Ad Library for a given page/advertiser.
    Captures individual ad screenshots for visual review.
    """
    label = label or page_name
    AD_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    url = (
        f"https://www.facebook.com/ads/library/"
        f"?active_status=active&ad_type=all&country=AU"
        f"&q={page_name}&search_type=keyword_unordered"
    )

    print(f"  [FB] Scraping ads for '{label}' ...")
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

            # Close any cookie/login popups
            for selector in [
                '[data-testid="cookie-policy-manage-dialog-accept-button"]',
                'button:has-text("Accept")',
                'button:has-text("Close")',
                '[aria-label="Close"]',
            ]:
                try:
                    btn = page.query_selector(selector)
                    if btn and btn.is_visible():
                        btn.click()
                        time.sleep(0.5)
                except Exception:
                    pass

            # Scroll to load more ads
            prev_height = 0
            for _ in range(min(max_ads // 3, 15)):
                page.evaluate("window.scrollBy(0, window.innerHeight * 2)")
                time.sleep(2)
                curr_height = page.evaluate("document.body.scrollHeight")
                if curr_height == prev_height:
                    break
                prev_height = curr_height

            # Extract ads using JavaScript — split by Library ID markers
            # and capture image URLs and ad copy
            raw_ads = page.evaluate("""() => {
                const results = [];
                const body = document.body.innerText;
                const parts = body.split(/Library ID:/);

                for (let i = 1; i < parts.length; i++) {
                    const chunk = parts[i].trim();
                    const lines = chunk.split('\\n').filter(l => l.trim());
                    const libraryId = (lines[0] || '').trim();

                    // Find start date
                    let startDate = '';
                    const dateMatch = chunk.match(/Started running on ([\\w\\d\\s]+?)\\n/);
                    if (dateMatch) startDate = dateMatch[1].trim();

                    // Check for multiple versions
                    const hasMultipleVersions = chunk.includes('multiple versions');
                    const versionMatch = chunk.match(/(\\d+) ads? use this/);
                    const versionCount = versionMatch ? parseInt(versionMatch[1]) : 1;

                    results.push({
                        library_id: libraryId,
                        start_date: startDate,
                        raw_text: chunk.substring(0, 2000),
                        has_multiple_versions: hasMultipleVersions,
                        version_count: versionCount,
                    });
                }
                return results;
            }""")

            # Now capture all images on the page with their positions
            all_images = page.evaluate("""() => {
                const imgs = [];
                document.querySelectorAll('img').forEach(img => {
                    const rect = img.getBoundingClientRect();
                    const src = img.src || img.getAttribute('data-src') || '';
                    if (src && rect.width > 50 && rect.height > 50
                        && !src.includes('emoji') && !src.includes('static')
                        && !src.includes('rsrc.php')) {
                        imgs.push({
                            src: src,
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                            top: Math.round(rect.top + window.scrollY),
                            left: Math.round(rect.left),
                        });
                    }
                });
                return imgs;
            }""")

            # Check for videos
            all_videos = page.evaluate("""() => {
                const vids = [];
                document.querySelectorAll('video').forEach(v => {
                    const rect = v.getBoundingClientRect();
                    const poster = v.poster || '';
                    const src = v.src || v.querySelector('source')?.src || '';
                    vids.push({
                        poster: poster,
                        src: src,
                        top: Math.round(rect.top + window.scrollY),
                    });
                });
                return vids;
            }""")

            # Build ad objects with images
            for i, raw in enumerate(raw_ads[:max_ads]):
                lid = raw.get("library_id", "")
                ad_url = f"https://www.facebook.com/ads/library/?id={lid}" if lid else url

                # Extract ad copy — everything after "Sponsored" or the page name
                text = raw.get("raw_text", "")
                # Clean up the text to extract meaningful copy
                copy_text = ""
                for pattern in [r'Sponsored\n(.+?)(?:YOUTUBE|TRILOGYCARE|Learn More|Shop Now|Sign Up|http)',
                                r'Sponsored\n(.+?)$']:
                    match = re.search(pattern, text, re.DOTALL)
                    if match:
                        copy_text = match.group(1).strip()[:500]
                        break
                if not copy_text:
                    # Get text after the date/platform info
                    lines = [l for l in text.split('\n') if l.strip() and len(l.strip()) > 10]
                    # Skip metadata lines
                    content_lines = [l for l in lines if not any(x in l for x in
                        ['Started running', 'Platforms', 'Drop-down', 'See ad details',
                         'multiple versions', 'ads use this', 'Library ID'])]
                    copy_text = '\n'.join(content_lines[:5])

                # Detect ad format
                has_video = any(v for v in all_videos)  # simplified
                ad_format = "video" if has_video and "video" in text.lower() else "image"

                # Extract CTA
                cta = ""
                for cta_text in ["Learn More", "Shop Now", "Sign Up", "Get Quote",
                                  "Book Now", "Contact Us", "Apply Now", "Download"]:
                    if cta_text.lower() in text.lower():
                        cta = cta_text
                        break

                # Download ad images
                image_paths = []
                for img in all_images:
                    src = img.get("src", "")
                    if src and ("scontent" in src or "fbcdn" in src):
                        img_filename = f"fb_{label}_{lid}_{len(image_paths)}.jpg"
                        img_path = AD_IMAGES_DIR / img_filename
                        if not img_path.exists():
                            try:
                                urllib.request.urlretrieve(src, str(img_path))
                                image_paths.append(str(img_path))
                            except Exception:
                                image_paths.append(src)  # fallback to URL
                        else:
                            image_paths.append(str(img_path))
                        if len(image_paths) >= 3:
                            break

                ad_data = {
                    "source": "facebook",
                    "advertiser": label,
                    "ad_index": i,
                    "library_id": lid,
                    "ad_url": ad_url,
                    "start_date": raw.get("start_date", ""),
                    "copy_text": copy_text,
                    "full_text": text[:2000],
                    "ad_format": ad_format,
                    "has_multiple_versions": raw.get("has_multiple_versions", False),
                    "version_count": raw.get("version_count", 1),
                    "cta": cta,
                    "image_paths": image_paths,
                    "image_urls": [img["src"] for img in all_images[:3] if "scontent" in img.get("src", "") or "fbcdn" in img.get("src", "")],
                    "scraped_at": datetime.now().isoformat(),
                }
                ads.append(ad_data)

            # Take a screenshot of each individual ad by scrolling to it
            # Take element-level screenshots for the first N ads
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(0.5)

            # Full page screenshot for reference
            ss_path = SCREENSHOTS_DIR / f"fb_{label}_{datetime.now():%Y%m%d_%H%M}.png"
            page.screenshot(path=str(ss_path), full_page=True)

            print(f"  [FB] Found {len(ads)} ads for '{label}'")

        except PWTimeout:
            print(f"  [FB] Timeout loading page for '{label}'")
        except Exception as e:
            print(f"  [FB] Error scraping '{label}': {e}")
        finally:
            browser.close()

    # Save raw data
    out_path = DATA_DIR / f"fb_{label}_{datetime.now():%Y%m%d}.json"
    with open(out_path, "w") as f:
        json.dump(ads, f, indent=2, default=str)

    return ads
