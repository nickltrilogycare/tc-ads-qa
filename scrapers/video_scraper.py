"""Video scraper - downloads ad videos from Facebook Ad Library using Playwright network interception."""
import ssl
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

VIDEOS_DIR = Path(__file__).parent.parent / "videos"
VIDEOS_DIR.mkdir(exist_ok=True)


def download_fb_video(library_id: str, label: str = "") -> dict:
    """Download video from a Facebook Ad Library page by intercepting CDN responses."""
    url = f"https://www.facebook.com/ads/library/?id={library_id}"
    video_urls: list[str] = []
    result: dict = {
        "library_id": library_id,
        "video_path": None,
        "thumbnail_path": None,
        "video_url": None,
    }

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

        # Intercept responses to find video URLs
        def handle_response(response):
            ct = response.headers.get("content-type", "")
            resp_url = response.url
            if (
                "video" in ct
                or ".mp4" in resp_url
                or ("fbcdn.net" in resp_url and "video" in resp_url)
            ):
                video_urls.append(resp_url)

        page = context.new_page()
        page.on("response", handle_response)

        try:
            page.goto(url, wait_until="networkidle", timeout=30_000)
            time.sleep(3)

            # Close popups (cookie consent, login walls, etc.)
            for sel in [
                'button:has-text("Accept")',
                'button:has-text("Close")',
                '[aria-label="Close"]',
            ]:
                try:
                    btn = page.query_selector(sel)
                    if btn and btn.is_visible():
                        btn.click()
                        time.sleep(0.5)
                except Exception:
                    pass

            # Try to click play on any <video> element
            try:
                video_el = page.query_selector("video")
                if video_el:
                    video_el.click()
                    time.sleep(3)
                    src = video_el.get_attribute("src") or ""
                    if src.startswith("http"):
                        video_urls.append(src)
            except Exception:
                pass

            # Try clicking common play-button selectors
            for sel in [
                '[aria-label="Play"]',
                'div[role="button"]:has(svg)',
                '[data-testid="play_button"]',
            ]:
                try:
                    btn = page.query_selector(sel)
                    if btn:
                        btn.click()
                        time.sleep(3)
                except Exception:
                    pass

            # Capture thumbnail screenshot
            safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)
            thumb_path = VIDEOS_DIR / f"thumb_{safe_label}_{library_id}.png"
            page.screenshot(path=str(thumb_path))
            result["thumbnail_path"] = str(thumb_path)

            # Download first video URL found (last is usually highest quality)
            if video_urls:
                video_path = VIDEOS_DIR / f"video_{safe_label}_{library_id}.mp4"
                best_url = video_urls[-1]
                result["video_url"] = best_url
                try:
                    # FB CDN requires SSL context bypass
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    opener = urllib.request.build_opener(
                        urllib.request.HTTPSHandler(context=ctx)
                    )
                    resp = opener.open(best_url)
                    with open(str(video_path), "wb") as vf:
                        vf.write(resp.read())
                    result["video_path"] = str(video_path)
                except Exception as e:
                    result["video_download_error"] = str(e)

        except Exception as e:
            result["error"] = str(e)
        finally:
            browser.close()

    return result


def batch_download_videos(ads: list[dict], max_videos: int = 20) -> list[dict]:
    """Download videos for ads that have library_ids and are video format."""
    results: list[dict] = []
    video_ads = [
        a for a in ads if a.get("ad_format") == "video" and a.get("library_id")
    ]

    for ad in video_ads[:max_videos]:
        lid = ad["library_id"]
        label = ad.get("advertiser", "unknown")
        print(f"  [Video] Downloading {label} / {lid}...")
        result = download_fb_video(lid, label)
        result["advertiser"] = label
        results.append(result)

    return results
