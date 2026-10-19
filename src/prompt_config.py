"""===============================================================================
Module: prompt_config.py
Description: Shared configuration and helpers for Instagram carousel prompts.
==============================================================================="""

import random

# Global resolution configuration optimized for vertical Instagram layouts.
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1350
ASPECT_RATIO = "4:5"

# Shared image-quality and typography constraints.
POSE_CONSTRAINT = (
    "Full tasteful apparel, natural posture, clean anatomy, realistic hands, "
    "clear subject separation, and high-contrast edge definition."
)

TYPOGRAPHY_CONSTRAINT = (
    "If rendering the quote inside the image, reproduce the supplied quote exactly, "
    "with no extra words, no misspellings, no quotation marks unless supplied, and "
    "no additional lettering. Use bold, highly legible white sans-serif typography "
    "with a subtle dark shadow or local contrast behind the text. Keep the quote "
    "within generous safe margins."
)

# Stable role guidance is combined with content-specific visual planning.
# The role is selected by position, while the visual metaphor comes from the text.
SLIDE_ROLE_GUIDANCE = {
    "opening": (
        "OPENING / HOOK: create the most immediately compelling composition in the "
        "sequence. Establish the emotional world and invite the viewer to continue."
    ),
    "development": (
        "DEVELOPMENT: deepen or complicate the idea. Show a distinct visual moment "
        "rather than repeating the opening composition."
    ),
    "realization": (
        "REALIZATION: communicate a shift in perspective, insight, or emotional "
        "turning point using a new composition or visual metaphor."
    ),
    "resolution": (
        "RESOLUTION: provide a visually satisfying ending that fits the actual text. "
        "It may feel calm, hopeful, empowering, bittersweet, or unresolved as needed."
    ),
}


def get_emotional_visual_modifier() -> str:
    """Return one atmospheric modifier to use consistently across a carousel."""
    modifiers = [
        "cinematic rim lighting, deep dramatic shadows, restrained focal highlights",
        "warm golden-hour light, atmospheric contrast, elegant modern styling",
        "dramatic volumetric lighting, clean depth, expressive but natural emotion",
        "soft ambient glow, high-contrast clarity, a thoughtful intimate atmosphere",
    ]
    return random.choice(modifiers)


def get_random_theme() -> str:
    """Select a theme for a new carousel."""
    themes = [
        "personal growth and overcoming obstacles",
        "inner peace and mindfulness",
        "courage and finding your purpose",
        "gratitude and appreciating small moments",
        "Love and Romance — emotional intimacy, unspoken feelings, longing, heartbreak, vulnerability, and the quiet realities of loving someone",
    ]
    selected = random.choice(themes)
    print(f"[THEME SELECTION] Randomly picked theme: '{selected}'")
    return selected


def get_random_style() -> str:
    """Return a visual style for the whole carousel, not a separate style per slide."""
    categories = [
        "realistic_photography",
        "realistic_animation",
        "digital_art_anime",
    ]
    chosen_category = random.choice(categories)

    if chosen_category == "realistic_animation":
        styles = [
            "high-quality stylized 3D animation, cinematic rim lighting, rich depth of field",
            "realistic 3D digital render, soft ambient occlusion, elegant wardrobe, bold contrast",
            "cinematic CGI animation, natural cloth physics, expressive lighting, striking focal depth",
            "photorealistic stylized 3D render, dramatic warm illumination, crisp edges",
        ]
        return random.choice(styles)

    if chosen_category == "realistic_photography":
        styles = [
            "high-contrast cinematic 35mm photography, golden-hour tones, rich moody shadows",
            "editorial lifestyle photography, atmospheric contrast, natural-looking people",
            "documentary-style portraiture, sharp focal clarity, balanced cinematic lighting",
            "moody high-end lifestyle photography, rich depth of field, cohesive color grading",
        ]
        return random.choice(styles)

    styles = [
        "modern anime style, clean high-contrast line art, dramatic backlighting, rich color",
        "sleek 3D digital art, luminous ambient glow, cinematic atmosphere, bold shadows",
        "stylized fantasy concept art, dynamic high-contrast lighting, rich color palette",
    ]
    return random.choice(styles)


def get_subject_and_instructions(active_theme: str) -> tuple[str, str]:
    """Determine a reusable subject description and continuity instructions."""
    relationship_keywords = ["love", "couple", "romantic", "connection", "relationship"]
    is_relationship_theme = any(
        keyword in active_theme.lower() for keyword in relationship_keywords
    )

    if is_relationship_theme:
        character_desc = "a couple dressed in stylish, modern, tasteful casual clothing"
        subject_instruction = (
            "Keep the same two people recognizable in every slide: preserve their "
            "facial features, hair, approximate age, clothing, and overall appearance. "
            "Natural body language; do not add or remove people without a narrative reason."
        )
    else:
        character_desc = "one central figure dressed in comfortable, tasteful modern clothing"
        subject_instruction = (
            "Keep the same main person recognizable in every slide: preserve facial "
            "features, hair, approximate age, clothing, and overall appearance. "
            "Natural body language and believable proportions."
        )

    return character_desc, subject_instruction


def get_slide_role(index: int, total: int) -> tuple[str, str]:
    """Return the narrative role and role guidance for a slide at a given position."""
    if index <= 1:
        key = "opening"
    elif index >= total:
        key = "resolution"
    elif index == 2:
        key = "development"
    else:
        key = "realization"

    return key, SLIDE_ROLE_GUIDANCE[key]


def build_carousel_style_block(
    chosen_style: str,
    emotional_modifier: str,
    character_desc: str,
    subject_instruction: str,
) -> str:
    """Build the shared visual identity reused in every slide prompt."""
    return f"""
SHARED CAROUSEL VISUAL IDENTITY
- Art direction: {chosen_style}
- Lighting and atmosphere: {emotional_modifier}
- Main subject: {character_desc}
- Subject continuity: {subject_instruction}
- Keep the same overall color grading, contrast, lighting logic, rendering medium,
  and level of realism throughout all slides.
- Use a vertical {TARGET_WIDTH}x{TARGET_HEIGHT} canvas ({ASPECT_RATIO}).
- {POSE_CONSTRAINT}
- Avoid watermarks, logos, borders, collages, split panels, and unrelated background text.
""".strip()
