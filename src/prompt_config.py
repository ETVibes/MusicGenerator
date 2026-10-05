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

# Shared quality and modesty constraints to ensure natural posture and appropriate attire
POSE_CONSTRAINT = (
    "ANATOMICAL & MODESTY QUALITY: Ensure full tasteful clothing on all human figures "
    "(e.g., elegant modern casual wear, sweater, jacket, trousers, modest dress). "
    "STRICTLY PROHIBITED: No nudity, no sheer or semi-transparent clothing, no exposed torsos, "
    "no bare chests, no revealing outfits, and no body paint. "
    "Ensure natural human anatomy, well-defined legs, clean leg positioning, "
    "and realistic seating/standing posture without distorted joints or extra limbs."
)

"""===============================================================================
    Returns an emotional visual modifier string to enhance scene atmosphere and depth.

    Returns:
        str: A randomly chosen atmospheric or emotional modifier phrase.
==============================================================================="""
def get_emotional_visual_modifier() -> str:
    """Returns an emotional visual modifier to enhance atmosphere and heart-touching depth."""
    modifiers = [
        "captured in a quiet, tender moment of vulnerability and deep reflection, dressed in cozy tasteful attire",
        "bathed in soft golden hour light, wearing elegant modest clothing, evoking warmth, hope, and quiet peace",
        "with candid, soulful expression, tastefully styled outfit, and intimate atmospheric depth",
        "surrounded by a serene, comforting environment with modest styling that evokes nostalgia and belonging",
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
        "realistic_animation",  # <-- Added realistic animation category
        "digital_art_anime",
        "vintage_retro",
        "minimalist_fine_art",
        "illustration_painting",
    ]
    chosen_category = random.choice(categories)

    if chosen_category == "realistic_animation":
        styles = [
            "hyper-realistic 3D animation style, Pixar-like photorealistic character rendering with soft cinematic lighting, fully clothed in warm autumn layers",
            "realistic 3D digital render with lifelike textures, soft ambient occlusion, elegant modest wardrobe, and subtle depth of field",
            "cinematic CGI animation style with realistic cloth physics on comfortable modern clothing, natural skin texture, and soft volumetric lighting",
            "photorealistic stylized 3D render, soft warm studio illumination, tasteful attire, lifelike hair detail, and cinematic atmospheric depth",
            "realistic animated feature film aesthetic with soft golden hour lighting, tastefully styled subjects, clean edge definition, and photorealistic environment textures",
        ]
        return f"A realistic animation style: {random.choice(styles)}"

    elif chosen_category == "realistic_photography":
        styles = [
            "cinematic 35mm photography with soft natural lighting, golden hour tones, and modest cozy apparel",
            "candid high-resolution portrait photo with soft bokeh, shallow depth of field, wearing clean modern knitwear",
            "moody editorial lifestyle photography with dramatic contrast, rich atmospheric depth, and stylish fully-covered outerwear",
            "documentary-style street photography shot on analog film with subtle grain and natural casual clothes",
            "dreamy golden-hour architectural photo with warm, ambient reflections and tastefully dressed subjects",
        ]
        return f"A realistic photo style: {random.choice(styles)}"

    elif chosen_category == "digital_art_anime":
        styles = [
            "vibrant anime style illustration with clean line art, tasteful modest outfits, dramatic backlighting, and soft lens flare",
            "modern 3D digital art render with sleek ambient glow, cozy layered apparel, soft shading, and cinematic atmosphere",
            "cozy Studio Ghibli-inspired digital scene with lush natural elements, modest character attire, and soft pastel lighting",
            "futuristic cyberpunk aesthetic with neon luminescence, stylish jacket and pants, and atmospheric mist",
            "stylized fantasy digital concept art with dynamic lighting, modest robe or attire, and rich color palettes",
        ]
        return f"A digital art style: {random.choice(styles)}"

    elif chosen_category == "vintage_retro":
        styles = [
            "retro 1970s film photo with warm faded film stock, gentle light leaks, analog texture, and classic 70s sweaters",
            "80s synthwave graphic novel art style with neon accents, high contrast, and retro street style clothing",
            "nostalgic 90s polaroid photo aesthetic with soft muted colors, film grain, and comfortable 90s casualwear",
            "vintage poster art with bold retro typography elements, modest clothing, and screen-print texture",
        ]
        return f"A vintage aesthetic style: {random.choice(styles)}"

    elif chosen_category == "minimalist_fine_art":
        styles = [
            "minimalist fine-art photo with clean negative space, simple modest dress, soft shadows, and subtle color palette",
            "abstract surrealist digital art with soft atmospheric gradients, tastefully clothed silhouette, and geometric balance",
            "scandi-inspired clean aesthetic with neutral earthy tones, comfortable lounge apparel, and gentle directional light",
            "monochromatic black-and-white fine art photography with high tonal range, modest styling, and deep contrast",
        ]
        return f"A minimalist fine art style: {random.choice(styles)}"

    else:  # illustration_painting
        styles = [
            "cozy watercolor painting with wet-on-wet textures, soft bleeding edges, modest outfit, and pastel tones",
            "textured oil painting aesthetic with visible palette knife strokes, elegant fully-covered clothing, and rich color blending",
            "whimsical storybook vector illustration with expressive detail, soft hand-drawn lines, and cozy layered clothing",
            "impressionist brushstroke painting with vibrant light play, modest dress, and painterly feel",
            "modern gouache illustration style with flat bold shapes, tasteful modern clothing, and hand-crafted textures",
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
        character_desc = "Exactly one couple (a man and a woman), both fully and modestly dressed in stylish casual clothes"
        subject_instruction = (
            "The SAME MAN and SAME WOMAN must appear across every image/panel. "
            "Ensure full tasteful clothing on both subjects (e.g., shirts, sweaters, jeans, or long pants). "
            "Ensure clear, anatomically correct body alignment, natural sitting postures, "
            "and distinct leg positions with no overlapping or tangled limbs."
        )
    else:
        character_desc = "A single central subject (either a man or a woman), fully and modestly clothed in comfortable apparel"
        subject_instruction = (
            "The EXACT SAME main person must appear as the sole focus across every image/panel. "
            "The subject MUST be fully clothed in respectful attire (e.g., cozy sweater, coat, jeans, dress). "
            "Maintain natural, anatomically correct posture and clear limb alignment."
        )
        
    return character_desc, subject_instruction