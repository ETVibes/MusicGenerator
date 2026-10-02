"""===============================================================================
Module: prompt_config.py
Description: Configuration and helper functions for generating image prompts,
             including resolution constants, quality constraints, random themes,
             visual styles, and subject consistency rules.
==============================================================================="""
from pathlib import Path
import random

# Global resolution configuration
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1350

# Shared quality constraints
POSE_CONSTRAINT = (
    "ANATOMICAL QUALITY: Ensure natural human anatomy, well-defined legs, clean leg positioning, "
    "and realistic seating posture. Avoid tangled, reversed, or overlapping legs, extra limbs, or distorted joints."
)

"""===============================================================================
    Returns an emotional visual modifier string to enhance scene atmosphere and depth.

    Returns:
        str: A randomly chosen atmospheric or emotional modifier phrase.
==============================================================================="""
def get_emotional_visual_modifier() -> str:
    """Returns an emotional visual modifier to enhance atmosphere and heart-touching depth."""
    modifiers = [
        "captured in a quiet, tender moment of vulnerability and deep reflection",
        "bathed in soft golden hour light, evoking warmth, hope, and quiet peace",
        "with candid, soulful expression and intimate, atmospheric depth",
        "surrounded by a serene, comforting environment that evokes nostalgia and belonging",
    ]
    return random.choice(modifiers)

"""===============================================================================
    Selects a random theme across diverse emotional and inspirational categories.

    Returns:
        str: The selected theme description.
==============================================================================="""
def get_random_theme() -> str:
    """Selects a random theme across diverse emotional and inspirational categories."""
    themes = [
        "self-strength and resilience",
        "inner peace and mindfulness",
        "personal growth and overcoming obstacles",
        "courage and finding your purpose",
        "emotional healing and hope",
        "deep love and romantic connection",
        "gratitude and appreciating small moments",
        "self-discovery and authenticity",
    ]
    selected = random.choice(themes)
    print(f"[THEME SELECTION] Randomly picked theme: '{selected}'")
    return selected

"""===============================================================================
    Returns a random visual style prompt selected across expanded aesthetic categories.

    Returns:
        str: A complete style description formatted with category prefix and specific details.
==============================================================================="""
def get_random_style() -> str:
    """Returns a random visual style prompt selected across expanded aesthetic categories."""
    categories = [
        "realistic_photography",
        "digital_art_anime",
        "vintage_retro",
        "minimalist_fine_art",
        "illustration_painting",
    ]
    chosen_category = random.choice(categories)

    if chosen_category == "realistic_photography":
        styles = [
            "cinematic 35mm photography with soft natural lighting and golden hour tones",
            "candid high-resolution portrait photo with soft bokeh and shallow depth of field",
            "moody editorial lifestyle photography with dramatic contrast and rich atmospheric depth",
            "documentary-style street photography shot on analog film with subtle grain",
            "dreamy golden-hour architectural photo with warm, ambient reflections",
        ]
        return f"A realistic photo style: {random.choice(styles)}"

    elif chosen_category == "digital_art_anime":
        styles = [
            "vibrant anime style illustration with clean line art, dramatic backlighting, and soft lens flare",
            "modern 3D digital art render with sleek ambient glow, soft shading, and cinematic atmosphere",
            "cozy Studio Ghibli-inspired digital scene with lush natural elements and soft pastel lighting",
            "futuristic cyberpunk aesthetic with neon luminescence and atmospheric mist",
            "stylized fantasy digital concept art with dynamic lighting and rich color palettes",
        ]
        return f"A digital art style: {random.choice(styles)}"

    elif chosen_category == "vintage_retro":
        styles = [
            "retro 1970s film photo with warm faded film stock, gentle light leaks, and analog texture",
            "80s synthwave graphic novel art style with neon accents and high contrast",
            "nostalgic 90s polaroid photo aesthetic with soft muted colors and film grain",
            "vintage vintage poster art with bold retro typography elements and screen-print texture",
        ]
        return f"A vintage aesthetic style: {random.choice(styles)}"

    elif chosen_category == "minimalist_fine_art":
        styles = [
            "minimalist fine-art photo with clean negative space, soft shadows, and subtle color palette",
            "abstract surrealist digital art with soft atmospheric gradients and geometric balance",
            "scandandi-inspired clean aesthetic with neutral earthy tones and gentle directional light",
            "monochromatic black-and-white fine art photography with high tonal range and deep contrast",
        ]
        return f"A minimalist fine art style: {random.choice(styles)}"

    else:  # illustration_painting
        styles = [
            "cozy watercolor painting with wet-on-wet textures, soft bleeding edges, and pastel tones",
            "textured oil painting aesthetic with visible palette knife strokes and rich color blending",
            "whimsical storybook vector illustration with expressive detail and soft hand-drawn lines",
            "impressionist brushstroke painting with vibrant light play and painterly feel",
            "modern gouache illustration style with flat bold shapes and hand-crafted textures",
        ]
        return f"An illustrative painting style: {random.choice(styles)}"

"""===============================================================================
    Determines character descriptions and visual consistency rules based on active theme keywords.

    Args:
        active_theme (str): The active thematic string used to determine character count and posture constraints.

    Returns:
        tuple[str, str]: A tuple containing:
            - character_desc (str): Concise subject description (single person vs. couple).
            - subject_instruction (str): Multi-panel visual consistency and anatomical placement guidelines.
==============================================================================="""
def get_subject_and_instructions(active_theme: str) -> tuple[str, str]:
    """Determines character descriptions and visual consistency rules based on active theme keywords."""
    is_relationship_theme = any(
        kw in active_theme.lower() for kw in ["love", "couple", "romantic", "connection"]
    )
    if is_relationship_theme:
        character_desc = "Exactly one couple (a man and a woman)"
        subject_instruction = (
            "The SAME MAN and SAME WOMAN must appear across every image/panel. "
            "Ensure clear, anatomically correct body alignment, natural sitting postures, "
            "and distinct leg positions with no overlapping or tangled limbs."
        )
    else:
        character_desc = "A single central subject (either a man or a woman)"
        subject_instruction = (
            "The EXACT SAME main person must appear as the sole focus across every image/panel with natural, "
            "anatomically correct posture and clear limb alignment."
        )
    return character_desc, subject_instruction