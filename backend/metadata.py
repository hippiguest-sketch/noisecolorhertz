"""SEO metadata generation (title / description / tags) per channel type.

Ported and adapted from the original factory's metadata_manager.py.
Template based — no AI, exactly as the user requested.
"""
from __future__ import annotations

import random

from presets import CHANNELS, duration_title

# ── noadsNoise ──────────────────────────────────────────────────────────────
NOISE_KEYWORDS = {
    "brown": {"tr": "Kahverengi Gurultu", "es": "Ruido Marron", "de": "Braunes Rauschen", "fr": "Bruit Brun"},
    "white": {"tr": "Beyaz Gurultu", "es": "Ruido Blanco", "de": "Weisses Rauschen", "fr": "Bruit Blanc"},
    "pink": {"tr": "Pembe Gurultu", "es": "Ruido Rosa", "de": "Rosa Rauschen", "fr": "Bruit Rose"},
    "rain": {"tr": "Yagmur Sesi", "es": "Sonido de Lluvia", "de": "Regengerausch", "fr": "Son de Pluie"},
    "grey": {"tr": "Gri Gurultu", "es": "Ruido Gris", "de": "Graues Rauschen", "fr": "Bruit Gris"},
    "violet": {"tr": "Mor Gurultu", "es": "Ruido Violeta", "de": "Violettes Rauschen", "fr": "Bruit Violet"},
    "green": {"tr": "Yesil Gurultu", "es": "Ruido Verde", "de": "Gruenes Rauschen", "fr": "Bruit Vert"},
}
TITLE_ADJ = {
    "brown": ["Deep", "Relaxing", "Soothing", "Calming", "Pure", "Smooth", "Gentle"],
    "white": ["Pure", "Soft", "Smooth", "Calming", "Gentle", "Relaxing", "Classic"],
    "pink": ["Soft", "Calming", "Balanced", "Gentle", "Relaxing", "Soothing", "Natural"],
    "rain": ["Gentle", "Relaxing", "Soothing", "Soft", "Calming", "Peaceful", "Natural"],
    "grey": ["Neutral", "Smooth", "Pure", "Calming", "Soft", "Gentle", "Deep"],
    "violet": ["Pure", "High", "Clear", "Crisp", "Sharp", "Calming", "Focused"],
    "green": ["Natural", "Organic", "Pure", "Calming", "Balanced", "Earthy", "Gentle"],
}
BENEFITS = [
    "Deep Sleep & Focus", "Sleep, Study & Calm", "Insomnia Relief & Relaxation",
    "Baby Sleep & Stress Relief", "ADHD Focus & Deep Rest", "Study, Work & Sleep",
    "Relaxation & Concentration", "Calm Mind & Better Sleep",
]


def _clean_tags(tags: list[str]) -> list[str]:
    seen, out, total = set(), [], 0
    for tag in tags:
        tag = str(tag).strip().lower()
        if not tag or tag in seen or len(tag) > 100:
            continue
        cost = len(tag) + (2 if " " in tag else 0) + (1 if out else 0)
        if total + cost > 450:
            continue
        seen.add(tag)
        out.append(tag)
        total += cost
    return out


def _noise_meta(variant: str, minutes: int) -> dict:
    v = CHANNELS["noadsNoise"]["variants"][variant]
    display = v["label"]
    adj = random.choice(TITLE_ADJ.get(variant, ["Pure"]))
    benefits = random.choice(BENEFITS)
    dur = duration_title(minutes)
    kw = NOISE_KEYWORDS.get(variant, {})
    low = display.lower()
    title = f"{adj} {display} Black Screen | {dur} | No Ads | {benefits}"
    description = f"""{title}

Welcome to @noadsNoise! High-quality {low} engineered for deep sleep, focus, study, and relaxation. Zero ads, zero interruptions.

WHAT IS {display.upper()}?
{display} is a carefully balanced sound frequency that masks background noise and creates a consistent sonic environment. Used for sleep improvement, ADHD focus, tinnitus relief, baby sleep and stress reduction.

WHY NO ADS?
This channel gives you uninterrupted sound sessions with zero ad breaks. No surprises. No interruptions.

GLOBAL SEARCH TERMS:
- English: {dur} {low} black screen no ads
- Turkish: {dur} {kw.get('tr', display)} siyah ekran reklamsiz
- Spanish: {dur} {kw.get('es', display)} pantalla negra sin anuncios
- German: {dur} {kw.get('de', display)} schwarzer bildschirm ohne werbung
- French: {dur} {kw.get('fr', display)} ecran noir sans publicite

SPECS: {display} | {dur} | Pure black screen | 44100 Hz stereo | No ads.

Subscribe to @noadsNoise for daily noise sounds for sleep, focus and relaxation."""
    tags = _clean_tags([
        f"{low} black screen", f"{low} no ads", f"{dur.lower()} {low}", f"{low} for sleep",
        f"{low} for focus", f"{low} for study", f"{low} sleep aid", f"{low} black screen no ads",
        "black screen no ads", f"{low} insomnia relief", f"{low} adhd focus", f"{low} baby sleep",
        f"{low} tinnitus relief", "sleep sounds no ads", "noise for sleep", "black screen sleep",
        "deep sleep sounds", low.replace(" ", ""), "no ads sleep sounds",
    ])
    return {"title": title, "description": description, "tags": tags}


# ── Noadscolors ──────────────────────────────────────────────────────────────
def _color_meta(variant: str, minutes: int) -> dict:
    v = CHANNELS["Noadscolors"]["variants"][variant]
    color = v["label"]
    dur = duration_title(minutes)
    low = color.lower()
    title = f"{dur} {color} Screen 🎨 4K Solid Color Background | No Sound | NO ADS"
    description = f"""{title}

Enjoy {dur.lower()} of a solid {low} screen in crisp 4K UHD. Clean background and ambient light, perfect for screen testing, device calibration, dead pixel check, mood lighting or minimalist relaxation.

No sound, no distractions, completely ad-free.

USES:
- Screen / dead-pixel test & color accuracy check
- Ambient mood lighting & chromatherapy
- Background for meditation and relaxation
- Bias lighting behind your TV or monitor

SPECS: Solid {color} | {dur} | 4K | No sound | No ads.

🔔 Subscribe to @Noadscolors for more color screens and ambient videos!"""
    tags = _clean_tags([
        f"{low} screen", f"{dur.lower()} {low} screen", f"4k {low} background", f"{low} screen no ads",
        "solid color screen", "color screen no sound", "screen test", "dead pixel test 4k",
        "color accuracy", f"{low} background", "chromatherapy", "mood lighting", "bias lighting",
        "meditation background", "no ads color screen",
    ])
    return {"title": title, "description": description, "tags": tags}


# ── Noadshertz ────────────────────────────────────────────────────────────────
def _hz_meta(variant: str, minutes: int) -> dict:
    v = CHANNELS["Noadshertz"]["variants"][variant]
    freq = v["freq"]
    purpose = v["purpose"]
    dur = duration_title(minutes)
    title = f"{freq}Hz {purpose} 🧘 Healing Frequency | {dur} | Black Screen | NO ADS"
    description = f"""{title}

{dur} of pure {freq}Hz healing frequency for {purpose.lower()}. Black screen, ad-free, ideal for meditation, deep sleep, manifestation and energy work.

ABOUT {freq}Hz:
The {freq}Hz frequency is part of the ancient Solfeggio scale, associated with {purpose.lower()}. Listen with headphones at a comfortable volume.

HOW TO USE:
- Meditation: sit comfortably, breathe deeply, let the tone guide you.
- Sleep: play softly through the night on a black screen.
- Focus & manifestation: use as a steady background anchor.

SPECS: Pure {freq}Hz sine tone | {dur} | Black screen | 44100 Hz stereo | No ads.

🔔 Subscribe to @Noadshertz for daily healing frequencies and solfeggio tones."""
    tags = _clean_tags([
        f"{freq}hz", f"{freq} hz", f"{freq}hz frequency", f"{freq}hz healing", "solfeggio frequency",
        "healing frequency", f"{freq}hz meditation", f"{freq}hz sleep", "meditation music no ads",
        "black screen frequency", purpose.lower(), "manifestation frequency", "energy healing",
        "chakra frequency", "no ads healing frequency",
    ])
    return {"title": title, "description": description, "tags": tags}


def generate_metadata(channel_key: str, variant: str, minutes: int) -> dict:
    ch_type = CHANNELS[channel_key]["type"]
    if ch_type == "noise":
        return _noise_meta(variant, minutes)
    if ch_type == "color":
        return _color_meta(variant, minutes)
    return _hz_meta(variant, minutes)
