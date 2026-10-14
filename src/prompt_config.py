"""===============================================================================
Module: prompt_config.py
Description: Configuration and helper functions for generating clean, high-impact image prompts,
             including resolution constants, quality constraints, random themes,
             visual styles, and subject consistency rules.
==============================================================================="""
from pathlib import Path
import random

# Global resolution configuration
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1350

# Streamlined, non-redundant quality and modesty constraints
POSE_CONSTRAINT = (
    "Style: Full tasteful apparel, natural posture, clean anatomy, high contrast legibility."
)

def get_emotional_visual_modifier() -> str:
    """Returns a concise atmospheric modifier to enhance depth without clutter."""
    modifiers = [
        "quiet moment of reflection, soft golden hour lighting, cozy modern attire",
        "serene atmosphere, warm cinematic tones, elegant casual wear",
        "candid soulful expression, rich atmospheric depth, stylish layered clothing",
        "peaceful comforting environment, gentle natural light, tasteful apparel",
    ]
    return random.choice(modifiers)

def get_random_theme() -> str:
    """Selects a random high-engagement theme optimized for Instagram views and shares."""
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
    """Returns a concise, punchy visual style prompt."""
    categories = [
        "realistic_photography",
        "realistic_animation",
        "digital_art_anime",
    # 10/14/26 - Removing a few categories    
    #    "vintage_retro",
    #    "minimalist_fine_art",
    #    "illustration_painting",
    ]
    chosen_category = random.choice(categories)

    if chosen_category == "realistic_animation":
        styles = [
            "Hyper-realistic 3D Pixar-style render, soft cinematic lighting, warm autumn layers",
            "Realistic 3D digital render, soft ambient occlusion, elegant wardrobe, subtle depth of field",
            "Cinematic CGI animation, realistic cloth physics, natural skin texture, soft volumetric lighting",
            "Photorealistic stylized 3D render, warm studio illumination, tasteful attire, clean edge definition",
        ]
        return random.choice(styles)

    elif chosen_category == "realistic_photography":
        styles = [
            "Cinematic 35mm photography, soft natural lighting, golden hour tones, cozy apparel",
            "Candid high-resolution portrait photo, soft bokeh, shallow depth of field, modern knitwear",
            "Editorial lifestyle photography, rich atmospheric depth, stylish outerwear",
            "Documentary-style street photography, analog film grain, casual clothing",
        ]
        return random.choice(styles)

    elif chosen_category == "digital_art_anime":
        styles = [
            "Vibrant modern anime style, clean line art, tasteful modest outfits, dramatic backlighting",
            "Sleek 3D digital art render, ambient glow, cozy apparel, cinematic atmosphere",
            "Cozy Studio Ghibli-inspired digital scene, lush natural elements, soft pastel lighting",
            "Stylized fantasy digital concept art, dynamic lighting, rich color palette",
        ]
        return random.choice(styles)

    elif chosen_category == "vintage_retro":
        styles = [
            "Retro 1970s film photo, warm faded stock, gentle light leaks, classic sweaters",
            "Nostalgic 90s polaroid photo aesthetic, soft muted colors, film grain, comfortable casualwear",
            "Vintage poster art, bold retro typography elements, modest clothing, screen-print texture",
        ]
        return random.choice(styles)

    elif chosen_category == "minimalist_fine_art":
        styles = [
            "Minimalist fine-art photo, clean negative space, simple modest dress, soft shadows",
            "Scandi-inspired clean aesthetic, neutral earthy tones, comfortable lounge apparel",
            "Monochromatic black-and-white fine art photography, high tonal range, deep contrast",
        ]
        return random.choice(styles)

    else:
        styles = [
            "Cozy watercolor painting, wet-on-wet textures, soft bleeding edges, pastel tones",
            "Textured oil painting, visible palette knife strokes, elegant fully-covered clothing",
            "Whimsical storybook vector illustration, hand-drawn lines, cozy layered clothing",
        ]
        return random.choice(styles)

def get_subject_and_instructions(active_theme: str) -> tuple[str, str]:
    """Determines concise character descriptions and consistency rules."""
    is_relationship_theme = any(
        kw in active_theme.lower() for kw in ["love", "couple", "romantic", "connection"]
    )
    
    if is_relationship_theme:
        character_desc = "A couple dressed in stylish modern casual wear"
        subject_instruction = "Consistent couple across panels, clean natural postures."
    else:
        character_desc = "A central figure dressed in comfortable, tasteful apparel"
        subject_instruction = "Consistent main subject, natural posture, clear framing."
        
    return character_desc, subject_instruction