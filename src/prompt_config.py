"""===============================================================================
Module: prompt_config.py
Description: Shared configuration and helpers for Instagram carousel prompts.
==============================================================================="""

import random
from PIL import Image, ImageDraw, ImageFont
import textwrap

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
        "growth and courage",
        "mindfulness and peace",
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

"""===============================================================================
    Loads an image, draws a wrapped quote onto it with a drop-shadow effect, 
    and saves the result.

    Args:
        image_path (str): Path to the source image file.
        quote (str): The quote text to draw on the image.
        output_path (str): Path where the final composited image will be saved.
        font_path (str, optional): Path to the TrueType font file (.ttf). Defaults to Montserrat.
        font_size (int, optional): Font size to use for the text. Defaults to 52.
        max_chars_per_line (int, optional): Maximum number of characters per wrapped line. Defaults to 28.

    Returns:
        str: The file path of the saved output image.
==============================================================================="""
def draw_quote_on_image(
    image_path: str,
    quote: str,
    output_path: str,
    font_path: str = "assets/Font/Montserrat-SemiBold.ttf",
    font_size: int = 52,
    max_chars_per_line: int = 28,
) -> str:

    # 1. Open image and prepare for drawing
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    width, height = img.size

    # 2. Load font (falls back to default bitmap font if no TTF path is provided)
    try:
        if font_path:
            font = ImageFont.truetype(font_path, font_size)
        else:
            # Attempt to use a common default system sans-serif font if available
            font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    # 3. Wrap text to fit nicely within horizontal margins
    wrapped_lines = textwrap.wrap(quote, width=max_chars_per_line)

    # 4. Calculate total block height for vertical centering
    # getmultilinebbox gives precise multi-line dimensions in modern Pillow versions
    bbox = draw.multiline_textbbox((0, 0), "\n".join(wrapped_lines), font=font, align="center")
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Position coordinates (Centered horizontally, lower-middle or center vertically)
    # For Instagram carousels, keeping text in the middle-lower zone avoids UI overlays.
    x = (width - text_width) / 2
    y = (height - text_height) / 2 + 100  # Offset slightly downward

    # 5. Draw text with a drop-shadow / outline for high contrast against photos
    shadow_offset = 3
    for line in wrapped_lines:
        # Measure line width for individual line alignment if needed
        line_bbox = draw.textbbox((0, 0), line, font=font)
        line_w = line_bbox[2] - line_bbox[0]
        line_x = x + (text_width - line_w) / 2  # Center-align individual lines

        # Draw dark shadow/outline offset
        draw.text(
            (line_x + shadow_offset, y + shadow_offset), 
            line, 
            font=font, 
            fill=(0, 0, 0, 180)
        )
        
        # Draw main crisp white text
        draw.text((line_x, y), line, font=font, fill=(255, 255, 255))
        
        # Advance y coordinate by line height (approximate via font metrics)
        y += font.size + 12

    # 6. Save final composite image
    img.save(output_path, "JPEG", quality=95, optimize=True)
    return output_path
    
"""===============================================================================
    Return tailored text prompt segments based on the selected theme.

    Args:
        theme (str): The theme selected for the carousel.

    Returns:
        tuple[str, str, str, str, str, str]: A tuple containing feel, voice, 
        slide_one, mid_slides, last_slide, and ban restrictions.
==============================================================================="""
def get_text_prompt_segments_by_theme(theme: str) -> tuple[str, str, str, str, str, str]:
    normalized_theme = (theme or "").strip().lower()

    if "love" in normalized_theme or "romance" in normalized_theme:
        feel = "positive, warm, and romantic"
        voice = "A warm, affectionate partner or close friend speaking with genuine care. Uplifting, tender, and reassuring. Use 'you'."
        slide_one = "A sweet, inviting hook about appreciating your person or a moment of connection."
        mid_slides = "Tender, positive observations about comfort, safety, or everyday affection."
        last_slide = "A heartwarming conclusion or gentle reminder worth saving or sending to a loved one."
        ban = "No heartbreak, no sadness, no nostalgia."
    elif "mindfulness" in normalized_theme or "peace" in normalized_theme:
        feel = "calm, grounding, and reflective"
        voice = "A gentle, quiet guide helping you pause and breathe. Soothing and centered. Use 'you'."
        slide_one = "A peaceful hook that invites the reader to drop their shoulders and slow down."
        mid_slides = "Simple observations about the present moment, breathing, and letting go of rush."
        last_slide = "A grounding takeaway offering stillness and quiet reassurance."
        ban = "No anxiety, no panic, no stress."
    elif "growth" in normalized_theme or "courage" in normalized_theme:
        feel = "encouraging, empowering, and strong"
        voice = "A supportive mentor cheering you on quietly from your corner. Inspiring and steady. Use 'you'."
        slide_one = "A bold, motivating hook about taking a small step forward."
        mid_slides = "Honest encouragement about building strength through daily effort."
        last_slide = "An empowering reminder of your own capability and resilience."
        ban = "No self-doubt, no giving up, no despair."
    else:
        feel = "warm, perceptive, and comforting"
        voice = "A quiet, perceptive friend talking to one person late at night. Warm, plain, specific. Use 'you'."
        slide_one = "A scroll-stopping hook about a small, relatable daily moment."
        mid_slides = "Quiet observations that develop the thought naturally."
        last_slide = "A comforting takeaway worth saving or sharing."
        ban = "No cynicism, no coldness, no judgment."

    return feel, voice, slide_one, mid_slides, last_slide, ban    