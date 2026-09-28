"""Channel / variant / duration presets for the 3 ambient YouTube channels.

Ported from the original production factory (noise_types.py + generators).
Every channel produces black-screen or solid-color videos via FFmpeg.
"""
from __future__ import annotations

# ── noadsNoise: FFmpeg anoisesrc based noise types ──────────────────────────
NOISE_TYPES = {
    "brown": {"filter": "anoisesrc=color=brown", "label": "Brown Noise", "thumb": "brown"},
    "white": {"filter": "anoisesrc=color=white", "label": "White Noise", "thumb": "white"},
    "pink": {"filter": "anoisesrc=color=pink", "label": "Pink Noise", "thumb": "pink"},
    "rain": {"filter": "anoisesrc=color=brown,aecho=0.8:0.9:60:0.4", "label": "Rain Noise", "thumb": "rain"},
    "grey": {"filter": "anoisesrc=color=white,highpass=f=300,lowpass=f=6000", "label": "Grey Noise", "thumb": "grey"},
    "violet": {"filter": "anoisesrc=color=violet", "label": "Violet Noise", "thumb": "violet"},
    "green": {"filter": "anoisesrc=color=pink,lowpass=f=1200", "label": "Green Noise", "thumb": "green"},
}

# ── Noadscolors: solid color screens, no sound ──────────────────────────────
COLOR_TYPES = {
    "red": {"hex": "0xE23636", "label": "Red", "thumb": "red"},
    "orange": {"hex": "0xF97316", "label": "Orange", "thumb": "orange"},
    "yellow": {"hex": "0xFACC15", "label": "Yellow", "thumb": "yellow"},
    "green": {"hex": "0x22C55E", "label": "Green", "thumb": "green"},
    "teal": {"hex": "0x14B8A6", "label": "Teal", "thumb": "blue"},
    "blue": {"hex": "0x3B82F6", "label": "Blue", "thumb": "blue"},
    "purple": {"hex": "0x8B5CF6", "label": "Purple", "thumb": "purple"},
    "pink": {"hex": "0xEC4899", "label": "Pink", "thumb": "pink"},
    "white": {"hex": "0xF5F5F5", "label": "White", "thumb": "white"},
    "black": {"hex": "0x0A0A0A", "label": "Black", "thumb": "black"},
}

# ── Noadshertz: solfeggio / healing frequencies (sine tone) ─────────────────
HZ_TYPES = {
    "174": {"freq": 174, "label": "174 Hz", "purpose": "Pain Relief & Foundation", "thumb": "deep space"},
    "285": {"freq": 285, "label": "285 Hz", "purpose": "Tissue & Cellular Healing", "thumb": "deep space"},
    "396": {"freq": 396, "label": "396 Hz", "purpose": "Release Fear & Guilt", "thumb": "violet"},
    "417": {"freq": 417, "label": "417 Hz", "purpose": "Facilitating Change", "thumb": "violet"},
    "432": {"freq": 432, "label": "432 Hz", "purpose": "Deep Calm & Harmony", "thumb": "green"},
    "528": {"freq": 528, "label": "528 Hz", "purpose": "DNA Repair & Miracles", "thumb": "green"},
    "639": {"freq": 639, "label": "639 Hz", "purpose": "Love & Relationships", "thumb": "pink"},
    "741": {"freq": 741, "label": "741 Hz", "purpose": "Detox & Cleansing", "thumb": "blue"},
    "852": {"freq": 852, "label": "852 Hz", "purpose": "Spiritual Awakening", "thumb": "purple"},
    "963": {"freq": 963, "label": "963 Hz", "purpose": "Crown Chakra & Oneness", "thumb": "purple"},
}

# Duration ladders (in MINUTES) per channel
NOISE_DURATIONS = [10, 20, 30, 60, 180, 360, 720, 1440]
COLOR_DURATIONS = [10, 15, 30, 60, 120]
HZ_DURATIONS = [10, 30, 60, 180, 480]

CHANNELS = {
    "noadsNoise": {
        "key": "noadsNoise",
        "name": "noadsNoise",
        "handle": "@noadsNoise",
        "type": "noise",
        "focus": "Rain, Thunder, White/Brown/Pink Noise, Dark Screen Sleep Sounds",
        "accent": "#38BDF8",
        "tagline": "SLEEP",
        "concept": "Ads-free natural soundscapes and pure noise for deep sleep, study and focus.",
        "variants": NOISE_TYPES,
        "durations": NOISE_DURATIONS,
        "has_audio": True,
    },
    "Noadscolors": {
        "key": "Noadscolors",
        "name": "no Ads COLOR",
        "handle": "@Noadscolors",
        "type": "color",
        "focus": "Solid Color Screens, Meditation, Chromatherapy & Color Gradients",
        "accent": "#F43F5E",
        "tagline": "NO SOUND",
        "concept": "Solid 4K color screens for relaxation, screen tests and color therapy.",
        "variants": COLOR_TYPES,
        "durations": COLOR_DURATIONS,
        "has_audio": False,
    },
    "Noadshertz": {
        "key": "Noadshertz",
        "name": "no Ads HERTZ",
        "handle": "@Noadshertz",
        "type": "hz",
        "focus": "Healing Frequencies (432Hz, 528Hz), Solfeggio, Binaural Beats",
        "accent": "#10B981",
        "tagline": "HEALING",
        "concept": "Solfeggio and healing frequencies for meditation, sleep and energy work.",
        "variants": HZ_TYPES,
        "durations": HZ_DURATIONS,
        "has_audio": True,
    },
}


def duration_label(minutes: int) -> tuple[str, str]:
    """Return (number, unit) big-thumbnail label for a duration in minutes."""
    if minutes < 60:
        return str(minutes), "MIN"
    if minutes % 60 == 0:
        hours = minutes // 60
        return str(hours), "HOUR" if hours == 1 else "HOURS"
    return f"{minutes/60:.1f}", "HOURS"


def duration_title(minutes: int) -> str:
    """Human title label e.g. '10 Hours', '30 Min'."""
    if minutes < 60:
        return f"{minutes} Min"
    if minutes == 60:
        return "1 Hour"
    if minutes % 60 == 0:
        return f"{minutes // 60} Hours"
    return f"{minutes/60:.1f} Hours"


def variant_meta(channel_key: str, variant: str) -> dict:
    ch = CHANNELS[channel_key]
    return ch["variants"].get(variant, {})
