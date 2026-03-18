"""Video Ad Analyzer - extracts frames and uses AI to analyze video ad content."""
import json
import base64
import shutil
import subprocess
from pathlib import Path

from openai import AzureOpenAI

from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION,
)

# Check tooling availability once at import time
_HAS_FFMPEG = shutil.which("ffmpeg") is not None
_HAS_FFPROBE = shutil.which("ffprobe") is not None

try:
    from PIL import Image  # noqa: F401
    _HAS_PILLOW = True
except ImportError:
    _HAS_PILLOW = False


def get_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
    )


def _get_video_duration_ffprobe(video_path: str) -> float:
    """Return video duration in seconds using ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
        ],
        capture_output=True, text=True, timeout=10,
    )
    return float(result.stdout.strip())


def _extract_frames_ffmpeg(video_path: str, num_frames: int, frames_dir: Path, prefix: str) -> list[str]:
    """Extract evenly-spaced frames using ffmpeg. Returns list of file paths."""
    try:
        duration = _get_video_duration_ffprobe(video_path)
    except Exception:
        duration = 30.0  # fallback

    interval = max(duration / (num_frames + 1), 0.5)
    frame_paths: list[str] = []

    for i in range(num_frames):
        timestamp = interval * (i + 1)
        out_path = frames_dir / f"{prefix}_frame{i}.png"
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-ss", str(timestamp),
                    "-i", video_path,
                    "-vframes", "1",
                    "-q:v", "2",
                    str(out_path),
                ],
                capture_output=True, timeout=10,
            )
            if out_path.exists() and out_path.stat().st_size > 0:
                frame_paths.append(str(out_path))
        except Exception:
            pass

    return frame_paths


def _extract_frames_pillow(video_path: str, num_frames: int, frames_dir: Path, prefix: str) -> list[str]:
    """Fallback frame extraction using Pillow + imageio (no ffmpeg needed).

    Requires: pip install imageio imageio-ffmpeg   (uses bundled ffmpeg binary)
    If imageio is also unavailable, returns an empty list.
    """
    try:
        import imageio.v3 as iio  # type: ignore
    except ImportError:
        # Last resort: just use the thumbnail screenshot if available
        return []

    try:
        frames_meta = iio.immeta(video_path, plugin="pyav")
        total_frames = frames_meta.get("n_frames", 100)
    except Exception:
        total_frames = 100

    step = max(total_frames // (num_frames + 1), 1)
    frame_paths: list[str] = []

    for i in range(num_frames):
        idx = step * (i + 1)
        try:
            frame = iio.imread(video_path, index=idx, plugin="pyav")
            img = Image.fromarray(frame)
            out_path = frames_dir / f"{prefix}_frame{i}.png"
            img.save(str(out_path))
            if out_path.exists() and out_path.stat().st_size > 0:
                frame_paths.append(str(out_path))
        except Exception:
            pass

    return frame_paths


def extract_frames(video_path: str, num_frames: int = 6) -> list[str]:
    """Extract evenly-spaced frames from video, return as base64 PNG strings.

    Prefers ffmpeg when available; falls back to Pillow + imageio.
    """
    vp = Path(video_path)
    if not vp.exists():
        return []

    frames_dir = vp.parent / "frames"
    frames_dir.mkdir(exist_ok=True)
    prefix = vp.stem

    # Choose extraction backend
    if _HAS_FFMPEG and _HAS_FFPROBE:
        frame_paths = _extract_frames_ffmpeg(video_path, num_frames, frames_dir, prefix)
    elif _HAS_PILLOW:
        frame_paths = _extract_frames_pillow(video_path, num_frames, frames_dir, prefix)
    else:
        # Neither available — return empty
        return []

    # Convert to base64
    frames_b64: list[str] = []
    for fp in frame_paths:
        try:
            data = Path(fp).read_bytes()
            frames_b64.append(base64.b64encode(data).decode())
        except Exception:
            pass

    return frames_b64


def analyze_video_ad(video_path: str, ad_context: dict | None = None) -> dict:
    """Analyze a video ad by extracting frames and sending to GPT-4.1."""
    client = get_client()
    ad_context = ad_context or {}
    frames = extract_frames(video_path)

    if not frames:
        return {"error": "Could not extract frames from video"}

    context_str = json.dumps(ad_context, default=str)[:500]
    advertiser = ad_context.get("advertiser", "Unknown")

    prompt = (
        "You are an expert video advertising analyst specialising in Australian "
        "aged care / Support at Home advertising.\n\n"
        f"Analyze this video ad based on the key frames below. The ad is from: {advertiser}\n\n"
        f"Context: {context_str}\n\n"
        "Provide a structured analysis covering:\n\n"
        "1. **Visual Storytelling** (0-25): Scene composition, transitions, production quality, emotional impact\n"
        "2. **Message Clarity** (0-25): Is the core message clear? Can viewers understand the value prop in the first 3 seconds (hook)?\n"
        "3. **Brand Presentation** (0-20): Logo placement, brand colors, consistency, professionalism\n"
        "4. **Call to Action** (0-15): Is there a clear CTA? Is it compelling? When does it appear?\n"
        "5. **Audience Relevance** (0-15): Does it resonate with older Australians / their families? Appropriate representation?\n\n"
        "Also identify:\n"
        "- The hook (first 3 seconds - what grabs attention?)\n"
        "- Key scenes/moments\n"
        "- Text overlays visible\n"
        "- Any people shown (demographics, authenticity)\n"
        "- Music/mood impression from visuals\n"
        "- What could be improved\n\n"
        "Return ONLY valid JSON:\n"
        "{\n"
        '  "video_score": <0-100>,\n'
        '  "category_scores": {\n'
        '    "visual_storytelling": {"score": <0-25>, "notes": "..."},\n'
        '    "message_clarity": {"score": <0-25>, "notes": "..."},\n'
        '    "brand_presentation": {"score": <0-20>, "notes": "..."},\n'
        '    "call_to_action": {"score": <0-15>, "notes": "..."},\n'
        '    "audience_relevance": {"score": <0-15>, "notes": "..."}\n'
        "  },\n"
        '  "hook_description": "what happens in the first 3 seconds",\n'
        '  "key_scenes": ["scene 1 description", "scene 2", "..."],\n'
        '  "text_overlays": ["any text visible on screen"],\n'
        '  "people_shown": "description of people in the ad",\n'
        '  "mood": "overall mood/tone",\n'
        '  "strengths": ["list"],\n'
        '  "improvements": ["list"],\n'
        '  "competitor_comparison": "how this compares to typical SAH advertising"\n'
        "}"
    )

    # Build multimodal content array
    content: list[dict] = [{"type": "text", "text": prompt}]

    for frame_b64 in frames[:6]:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{frame_b64}",
                "detail": "low",
            },
        })

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[{"role": "user", "content": content}],
            temperature=0.3,
            max_tokens=2000,
        )

        result_text = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        if result_text.startswith("```"):
            result_text = result_text.split("\n", 1)[1]
            if result_text.endswith("```"):
                result_text = result_text[:-3].strip()

        return json.loads(result_text)

    except json.JSONDecodeError:
        return {"error": "AI response was not valid JSON", "raw": result_text}
    except Exception as e:
        return {"error": str(e)}
