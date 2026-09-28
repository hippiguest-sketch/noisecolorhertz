"""FFmpeg video/audio rendering + Pillow thumbnail generation.

Ported from the original factory (video_generator.py + thumbnail_generator.py).
For long-form videos we render a real preview clip (capped) that represents the
full production; the intended duration is stored in metadata.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Callable, Optional

from PIL import Image, ImageDraw, ImageFont

from presets import CHANNELS, duration_label

GENERATED_DIR = Path(__file__).parent / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

FONT_PATH = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"

# Cap the physically-rendered length so the demo stays snappy. The metadata
# still advertises the full intended duration (e.g. "10 Hours").
RENDER_CAP_SECONDS = 18

THUMB_COLORS = {
    "green": (0, 177, 64), "orange": (255, 115, 0), "purple": (118, 0, 190),
    "red": (220, 20, 60), "blue": (0, 102, 204), "yellow": (255, 204, 0),
    "white": (245, 245, 245), "grey": (100, 100, 100), "black": (15, 15, 15),
    "brown": (120, 60, 30), "pink": (255, 145, 180), "violet": (138, 43, 226),
    "rain": (45, 55, 70), "deep space": (8, 12, 35),
}
NO_ADS_BADGE = (220, 20, 60)


def _job_dir(job_id: str) -> Path:
    d = GENERATED_DIR / job_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _noise_audio_input(noise_filter: str, seconds: int) -> str:
    src, sep, rest = noise_filter.partition(",")
    src = f"{src}:duration={seconds}:sample_rate=44100:amplitude=0.55"
    return f"{src}{sep}{rest}"


def render_video(spec: dict, job_id: str, log: Optional[Callable[[str], None]] = None) -> Optional[str]:
    """Render an mp4 (video + optional audio) for the given job spec."""
    log = log or (lambda _m: None)
    ch = CHANNELS[spec["channel_key"]]
    ch_type = ch["type"]
    is_short = spec["format"] == "short"
    seconds = min(int(spec.get("render_seconds", RENDER_CAP_SECONDS)), 120)
    size = "720x1280" if is_short else "1280x720"
    w, h = (720, 1280) if is_short else (1280, 720)
    out = str(_job_dir(job_id) / "video.mp4")

    if ch_type == "color":
        color_hex = ch["variants"][spec["variant"]]["hex"]
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c={color_hex}:s={size}:r=15:d={seconds}",
            "-t", str(seconds), "-c:v", "libx264", "-preset", "ultrafast",
            "-tune", "stillimage", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out,
        ]
    else:
        # noise or hz: black background + soft waveform overlay + audio
        if ch_type == "noise":
            audio = _noise_audio_input(ch["variants"][spec["variant"]]["filter"], seconds)
        else:  # hz
            freq = ch["variants"][spec["variant"]]["freq"]
            audio = f"sine=frequency={freq}:sample_rate=44100:duration={seconds}"
        accent = "0x10B981" if ch_type == "hz" else "0x38BDF8"
        wave_h = int(h * 0.35)
        wave_y = int(h * 0.62)
        fcomplex = (
            f"[1:a]showwaves=s={w}x{wave_h}:mode=line:colors={accent}:scale=sqrt:draw=full,"
            f"format=rgba,colorchannelmixer=aa=0.35[waves];"
            f"[0:v][waves]overlay=0:{wave_y}:format=auto[v]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=black:s={size}:r=15:d={seconds}",
            "-f", "lavfi", "-i", audio,
            "-filter_complex", fcomplex,
            "-map", "[v]", "-map", "1:a",
            "-t", str(seconds), "-c:v", "libx264", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest",
            "-movflags", "+faststart", out,
        ]

    log(f"ffmpeg render start ({size}, {seconds}s)")
    try:
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=180)
        if r.returncode != 0:
            log("ffmpeg ERROR: " + r.stderr.decode(errors="replace")[-400:])
            return None
    except subprocess.TimeoutExpired:
        log("ffmpeg TIMEOUT")
        return None
    if not (os.path.exists(out) and os.path.getsize(out) > 0):
        return None
    log(f"video ready: {os.path.getsize(out)//1024} KB")
    return out


def _font(size: int):
    size = max(8, int(size))
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()


def render_thumbnail(spec: dict, job_id: str, log: Optional[Callable[[str], None]] = None) -> Optional[str]:
    """Draw a v6-style thumbnail: big duration number, dotted line, right lines, NO ADS badge."""
    log = log or (lambda _m: None)
    ch = CHANNELS[spec["channel_key"]]
    is_short = spec["format"] == "short"
    W, H = (1080, 1920) if is_short else (1280, 720)

    v = ch["variants"][spec["variant"]]
    thumb_key = v.get("thumb", "black")
    bg = THUMB_COLORS.get(thumb_key, (15, 15, 15))
    txt = (15, 15, 15) if thumb_key in ("white", "yellow") else (255, 255, 255)

    number, unit = duration_label(spec["duration_minutes"])
    variant_label = v["label"].upper().replace(" NOISE", "").replace("HZ", "")
    if ch["type"] == "hz":
        variant_label = f"{v['freq']}HZ"
    right_lines = [unit, variant_label, ch["tagline"]]

    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)

    main_size = int(W * (0.30 if is_short else 0.42))
    right_size = int(W * (0.075 if is_short else 0.075))
    ads_size = int(right_size * 0.7)
    f_main = _font(main_size)
    f_right = _font(right_size)
    f_ads = _font(ads_size)

    main_w = d.textlength(str(number), font=f_main)
    right_w = max(d.textlength(l, font=f_right) for l in right_lines)
    gap = int(W * 0.05)
    total_w = main_w + gap * 2 + right_w
    start_x = (W - total_w) / 2
    main_cx = start_x + main_w / 2
    line_x = start_x + main_w + gap
    right_x = line_x + gap
    cy = H / 2
    line_spacing = right_size * 1.25
    y0 = cy - line_spacing

    # dotted vertical divider
    y = int(cy - line_spacing * 1.7)
    while y < cy + line_spacing * 1.7:
        d.line((line_x, y, line_x, min(y + 16, int(cy + line_spacing * 1.7))), fill=txt, width=max(6, W // 160))
        y += 28

    d.text((main_cx, cy), str(number), font=f_main, fill=txt, anchor="mm")
    for line, yy in zip(right_lines, [y0, y0 + line_spacing, y0 + line_spacing * 2]):
        d.text((right_x, yy), line, font=f_right, fill=txt, anchor="lm")

    # NO ADS badge
    badge_y = y0 + line_spacing * 2.9
    bbox = d.textbbox((0, 0), "NO ADS", font=f_ads)
    aw, ah = bbox[2] - bbox[0], bbox[3] - bbox[1]
    px, py = int(ads_size * 0.35), int(ads_size * 0.28)
    d.rectangle((right_x - px, badge_y - py, right_x + aw + px, badge_y + ah + py), fill=NO_ADS_BADGE)
    d.text((right_x, badge_y - bbox[1]), "NO ADS", font=f_ads, fill=(255, 255, 255))

    out = str(_job_dir(job_id) / "thumb.jpg")
    img.save(out, "JPEG", quality=92)
    log("thumbnail ready")
    return out
