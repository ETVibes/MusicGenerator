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
        "soft golden window light with a gentle warm glow and light, airy shadows",
        "warm sunlit atmosphere with a faint lens glow and lifted shadows",
        "gentle backlight creating a soft halo, bright open background with warm highlights",
    ]
    return random.choice(modifiers)
    
# Clichés the writing model should avoid in any post type. Edit freely: start short and
# add phrases you actually see in the outputs.
BANNED_PHRASES = [
    "you are enough",
    "journey",
    "the universe",
    "trust the process",
    "healing isn't linear",
    "self-love",
    "believe in yourself",
    "just breathe",
]

def get_random_theme() -> str:
    """Select a theme for a new carousel."""
    themes = [
        "personal growth and overcoming obstacles",
        "inner peace and mindfulness",
        "courage and finding your purpose",
        "gratitude and appreciating small moments",
        "Love and Romance",
    ]
    selected = random.choice(themes)
    print(f"[THEME SELECTION] Randomly picked theme: '{selected}'")
    return selected


def get_random_style() -> str:
    """Return a visual style for the whole carousel, not a separate style per slide."""
    styles = [
        "cinematic 35mm film photography, soft film grain, shallow depth of field, warm natural color, bright and uplifting",
        "editorial lifestyle photography, golden-hour light, honey and cream tones, airy and gentle",
        "soft morning-light photography, pale sky blue and warm peach, calm and luminous",
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
- The mood must feel warm, hopeful and calm even when the quote is bittersweet; shadows stay soft and lifted.
- {POSE_CONSTRAINT}
- Avoid watermarks, logos, borders, collages, split panels, and unrelated background text.
""".strip()