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
    "clear subject separation, high-contrast edge definition, and "
    "complete anatomical integrity (no accidental cropping of heads, faces, or limbs "
    "within the frame)."
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

THEME_PRESETS = {
    "love and romance": {
        "style": "high-end editorial lifestyle photography, soft romantic tones, intimate framing, cream and warm amber color palette, elegant and timeless",
        "modifier": "warm sunlit atmosphere with a faint golden hour lens glow and soft, lifted shadows",
    },
    "mindfulness and peace": {
        "style": "minimalist aesthetic documentary photography, tranquil atmosphere, muted organic earth tones, calm and deeply grounding composition",
        "modifier": "gentle morning window light creating a soft halo, clean airy background with peaceful highlights",
    },
    "growth and courage": {
        "style": "cinematic 35mm documentary film photography, rich organic textures, moody depth of field, striking contrast, powerful and inspiring",
        "modifier": "dramatic directional sunlight cutting through shadows with an empowering, cinematic warmth",
    },
    "gratitude and appreciating small moments": {
        "style": "cozy aesthetic lifestyle photography, tactile textures, warm beige and soft terracotta tones, candid and deeply nostalgic",
        "modifier": "soft indoor golden hour light filtering through sheer curtains, creating a quiet and cherished mood",
    },
}

def get_style_and_modifier_for_theme(theme: str) -> tuple[str, str]:
    """Return a curated style and emotional modifier pair based on the theme."""
    normalized = (theme or "").strip().lower()
    
    # Look for a matching theme key, or fall back to a default pair
    preset = THEME_PRESETS.get(normalized)
    if not preset:
        # Fallback if a theme doesn't match an exact key
        preset = {
            "style": "editorial lifestyle photography, golden-hour light, honey and cream tones, airy and gentle",
            "modifier": "warm sunlit atmosphere with a faint lens glow and lifted shadows",
        }
    
    return preset["style"], preset["modifier"]

def get_random_theme() -> str:
    """Select a theme for a new carousel."""
    themes = [
        "growth and courage",
        "mindfulness and peace",
        "courage and finding your purpose",
        "gratitude and appreciating small moments",
        "love and romance",
    ]
    selected = random.choice(themes)
    print(f"[THEME SELECTION] Randomly picked theme: '{selected}'")
    return selected

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
    """Loads an image, draws a wrapped quote onto it with separate styling for a CTA, and saves the result."""
    # 1. Open image and prepare for drawing
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    width, height = img.size

    # 2. Load font
    try:
        if font_path:
            font = ImageFont.truetype(font_path, font_size)
        else:
            font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    # 3. Separate main text from CTA if a double newline delimiter exists
    parts = quote.split("\n\n")
    main_text = parts[0]
    cta_text = parts[1] if len(parts) > 1 else None

    main_lines = textwrap.wrap(main_text, width=max_chars_per_line)
    cta_lines = textwrap.wrap(cta_text, width=max_chars_per_line) if cta_text else []

    # 4. Calculate total block height for vertical centering
    all_lines = main_lines + ([""] + cta_lines if cta_lines else [])
    bbox = draw.multiline_textbbox((0, 0), "\n".join(all_lines), font=font, align="center")
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Position coordinates (Centered horizontally, lower-middle or center vertically)
    x = (width - text_width) / 2
    y = (height - text_height) / 2 + 100  # Offset slightly downward

    shadow_offset = 3

    # 5. Draw main narrative text lines (White)
    for line in main_lines:
        line_bbox = draw.textbbox((0, 0), line, font=font)
        line_w = line_bbox[2] - line_bbox[0]
        line_x = x + (text_width - line_w) / 2

        # Draw dark shadow/outline offset
        draw.text(
            (line_x + shadow_offset, y + shadow_offset), 
            line, 
            font=font, 
            fill=(0, 0, 0, 180)
        )
        # Draw main crisp white text
        draw.text((line_x, y), line, font=font, fill=(255, 255, 255))
        y += font.size + 12

    # 6. Draw CTA lines on a new block with a different color (Gold / Yellow #FFD700)
    if cta_lines:
        y += 16  # Add extra spacing buffer before the CTA paragraph
        cta_color = (255, 215, 0)

        for line in cta_lines:
            line_bbox = draw.textbbox((0, 0), line, font=font)
            line_w = line_bbox[2] - line_bbox[0]
            line_x = x + (text_width - line_w) / 2

            # Draw dark shadow/outline offset
            draw.text(
                (line_x + shadow_offset, y + shadow_offset), 
                line, 
                font=font, 
                fill=(0, 0, 0, 180)
            )
            # Draw colored CTA text
            draw.text((line_x, y), line, font=font, fill=cta_color)
            y += font.size + 12

    # 7. Save final composite image
    img.save(output_path, "JPEG", quality=95, optimize=True)
    return output_path
    
def draw_quote_on_image_old(
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
        voice = "Speaking directly about an intimate bond or a shared moment between two people. Relatable, tender, and deeply personal. Use 'you'."
        slide_one = "A sharp, highly relatable hook about the comfort of being with your favorite person."
        mid_slides = "Deepening observations about quiet glances, shared safety, and effortless love."
        last_slide = "A heartwarming resolution that naturally compels someone to send it to their partner or best friend."
        ban = "No heartbreak, no sadness, no nostalgia."
    elif "mindfulness" in normalized_theme or "peace" in normalized_theme:
        feel = "calm, grounding, and reflective"
        voice = "A gentle, shared reflection on finding peace alongside someone else or navigating a busy world together. Use 'you'."
        slide_one = "A hook addressing a shared feeling of exhaustion or wanting to slow down with someone."
        mid_slides = "Simple observations about finding a safe harbor in another person or a quiet space."
        last_slide = "A grounding takeaway with a clear invitation to drop it in a group chat or send to a friend."
        ban = "No anxiety, no panic, no stress."
    elif "growth" in normalized_theme or "courage" in normalized_theme:
        feel = "encouraging, empowering, and strong"
        voice = "A supportive voice speaking to someone you care about who is fighting silent battles. Inspiring and steady. Use 'you'."
        slide_one = "A bold hook about the person who stays and shows up through hard seasons."
        mid_slides = "Honest encouragement about building strength together or being someone's safe place."
        last_slide = "An empowering reminder to share with someone who needs a reminder of their inner strength."
        ban = "No self-doubt, no giving up, no despair."
    else:
        feel = "warm, perceptive, and comforting"
        voice = "A quiet, perceptive friend talking about the unspoken dynamics between close people. Warm and specific. Use 'you'."
        slide_one = "A scroll-stopping hook about a shared unspoken feeling or relationship dynamic."
        mid_slides = "Quiet observations that develop the emotional bond naturally."
        last_slide = "A comforting takeaway built to be shared with a close friend."
        ban = "No cynicism, no coldness, no judgment."

    return feel, voice, slide_one, mid_slides, last_slide, ban
    
def get_text_prompt_segments_by_theme_old(theme: str) -> tuple[str, str, str, str, str, str]:
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