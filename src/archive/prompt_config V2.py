"""===============================================================================
Module: prompt_config.py
Description: Configuration and helper functions for generating clean, high-impact image prompts,
             including resolution constants, quality constraints, optimized top themes,
             visual styles, and subject consistency rules.
==============================================================================="""
from pathlib import Path
import random

# Global resolution configuration optimized for vertical Instagram layouts
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1350

# Streamlined constraint ensuring clean anatomy and high legibility
POSE_CONSTRAINT = (
    "Style: Full tasteful apparel, natural posture, clean anatomy, high contrast edge definition."
)

def get_emotional_visual_modifier() -> str:
    """Returns a concise cinematic modifier for high atmospheric depth."""
    modifiers = [
        "cinematic rim lighting, deep dramatic shadows, rich focal pop",
        "warm golden hour rays, high contrast atmosphere, elegant modern styling",
        "dramatic volumetric lighting, clean studio depth, soulful expression",
        "soft ambient glow, high-contrast clarity, comforting environment",
    ]
    return random.choice(modifiers)

def get_random_theme() -> str:
    """Selects from top-tier high-engagement themes proven to maximize views and shares."""
    themes = [
        "personal growth and overcoming obstacles",
        "inner peace and mindfulness",
        "courage and finding your purpose",
        "gratitude and appreciating small moments",
    ]
    selected = random.choice(themes)
    print(f"[THEME SELECTION] Randomly picked theme: '{selected}'")
    return selected

def get_random_style() -> str:
    """Returns a high-contrast, thumb-stopping visual style prompt."""
    categories = [
        "realistic_photography",
        "realistic_animation",
        "digital_art_anime",
    ]
    chosen_category = random.choice(categories)

    if chosen_category == "realistic_animation":
        styles = [
            "Hyper-realistic 3D Pixar-style render, high-contrast cinematic rim lighting, rich depth of field",
            "Realistic 3D digital render, sharp ambient occlusion, elegant wardrobe, bold visual contrast",
            "Cinematic CGI animation, realistic cloth physics, vibrant lighting, striking focal depth",
            "Photorealistic stylized 3D render, dramatic warm illumination, tasteful attire, crisp edges",
        ]
        return random.choice(styles)

    elif chosen_category == "realistic_photography":
        styles = [
            "High-contrast cinematic 35mm photography, dramatic golden hour tones, rich moody shadows",
            "Striking editorial lifestyle photography, deep atmospheric contrast, stylish outerwear",
            "Documentary-style portraiture, sharp focal clarity, cinematic lighting balance",
            "Moody high-end lifestyle capture, rich depth of field, vibrant color grading",
        ]
        return random.choice(styles)

    else:  # digital_art_anime
        styles = [
            "Vibrant modern anime style, clean high-contrast line art, dramatic backlighting, rich color pop",
            "Sleek 3D digital art render, luminous ambient glow, cinematic atmosphere, bold shadows",
            "Stylized fantasy digital concept art, dynamic high-contrast lighting, rich color palette",
        ]
        return random.choice(styles)

def get_subject_and_instructions(active_theme: str) -> tuple[str, str]:
    """Determines concise character descriptions and consistency rules."""
    is_relationship_theme = any(
        kw in active_theme.lower() for kw in ["love", "couple", "romantic", "connection"]
    )
    
    if is_relationship_theme:
        character_desc = "A couple dressed in stylish modern casual wear"
        subject_instruction = "Consistent couple across panels, clean natural postures, sharp framing."
    else:
        character_desc = "A central figure dressed in comfortable, tasteful apparel"
        subject_instruction = "Consistent main subject, natural posture, striking central framing."
        
    return character_desc, subject_instruction