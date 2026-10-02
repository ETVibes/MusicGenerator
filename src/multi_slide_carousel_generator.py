"""===============================================================================
Module: multi_slide_carousel_generator.py
Description: Generates multi-slide Instagram carousel posts. Uses Gemini text 
             models to construct cohesive script progressions and multi-modal 
             Gemini image generation models to render sequential visual slides 
             maintaining character and visual style continuity.
==============================================================================="""
from datetime import datetime
import io
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image

from .prompt_config import (
    POSE_CONSTRAINT,
    TARGET_HEIGHT,
    TARGET_WIDTH,
    get_emotional_visual_modifier,
    get_random_style,
    get_random_theme,
    get_subject_and_instructions,
)

"""===============================================================================
    Generates a multi-slide Instagram carousel post with script flow and visual continuity.

    Args:
        theme (str, optional): The thematic concept for the post. Defaults to a random theme if None.
        num_slides (int, optional): The number of carousel slides to generate. Defaults to 4.

    Returns:
        tuple[list[str], list[str], str, str, str]: A tuple containing:
            - generated_image_paths (list[str]): Saved filepaths of generated JPEG images.
            - slide_quotes (list[str]): Extracted quote text lines for each slide.
            - explanation (str): Caption narrative explanation.
            - hashtags (str): Generated Instagram hashtag block.
            - music_recommendation (str): Recommended background music audio track.

    Raises:
        RuntimeError: If image generation or processing fails for any individual slide.
==============================================================================="""
def generate_multi_slide_carousel(
    theme: str = None, num_slides: int = 4
) -> tuple[list[str], list[str], str, str, str]:
    """Generates an Instagram multi-slide carousel post with visual continuity across separate images."""
    client = genai.Client()
    active_theme = theme if theme else get_random_theme()
    chosen_style = get_random_style()
    character_desc, subject_instruction = get_subject_and_instructions(active_theme)
    emotional_modifier = get_emotional_visual_modifier()

    # 1. Script Generation for Carousel
    text_prompt = (
        f"Write an Instagram carousel post caption package for the theme '{active_theme}'.\n"
        f"1. Generate {num_slides} flowing, modern, and deeply reflective sentences (6 to 12 words per slide) separated by '|'. "
        f"The text should sound like a personal journal entry or modern voice memo rather than short poetry. "
        f"Follow an emotional narrative progression:\n"
        f"   - Slide 1: A vulnerable, modern realization about protection, overthinking, or fear.\n"
        f"   - Slide 2: The turning point where soft tenderness or quiet understanding enters.\n"
        f"   - Slide 3: The active decision to unlearn old habits and embrace connection.\n"
        f"   - Slide 4: A grounding, reassuring closing thought about what truly matters.\n"
        f"Use natural, conversational modern language. Avoid archaic or overly poetic tropes.\n"
        f"2. A 2-3 sentence inspiring overall caption explanation reflecting deeply on this journey.\n"
        f"3. 6 to 9 relevant, high-engagement Instagram hashtags tailored specifically to '{active_theme}' (always include #thisisdailywhisper).\n"
        f"4. A suggested song title and artist available on Instagram Audio that matches the mood.\n\n"
        f"Format strictly as:\n"
        f"QUOTE: <slide 1 quote | slide 2 quote | slide 3 quote ...>\n"
        f"EXPLANATION: <your explanation>\n"
        f"HASHTAGS: <your hashtags separated by spaces>\n"
        f"MUSIC: <song name - artist name or genre keyword search>"
    )
    
    sentence_response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=text_prompt,
    )
    raw_text = sentence_response.text.strip()

    quote_raw = ""
    explanation = ""
    hashtags = "#thisisdailywhisper #inspiration #motivation"
    music_recommendation = ""

    for line in raw_text.splitlines():
        if line.startswith("QUOTE:"):
            quote_raw = line.replace("QUOTE:", "").strip().replace('"', "")
        elif line.startswith("EXPLANATION:"):
            explanation = line.replace("EXPLANATION:", "").strip()
        elif line.startswith("HASHTAGS:"):
            hashtags = line.replace("HASHTAGS:", "").strip()
        elif line.startswith("MUSIC:"):
            music_recommendation = line.replace("MUSIC:", "").strip()

    slide_quotes = [q.strip() for q in quote_raw.split("|") if q.strip()]

    while len(slide_quotes) < num_slides:
        slide_quotes.append(f"Slide {len(slide_quotes) + 1}")
    slide_quotes = slide_quotes[:num_slides]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("output") / "Carousel_Posts" / f"carousel_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_image_paths = []
    first_slide_image = None

    # 2. Sequential Slide Rendering
    for idx, slide_text in enumerate(slide_quotes, 1):
        if idx == 1:
            image_prompt = (
                f"{chosen_style} themed around '{active_theme}'. "
                f"Slide {idx} of {num_slides} in a cohesive Instagram carousel sequence. "
                f"MAIN SUBJECT & CHARACTER ANCHOR: {character_desc}, {emotional_modifier}. "
                f"VISUAL CONTINUITY: {subject_instruction} Establish clear facial features, hair style/color, age, and clothing. "
                f"{POSE_CONSTRAINT} "
                f"SCENE 1 (ISOLATION / TENSION): Visually depict the emotional distance and vulnerability for: '{slide_text}'. "
                f"TYPOGRAPHY & TEXT OVERLAY: Overlay the exact text string: \"{slide_text}\" in clean, bold, white sans-serif typography. "
                f"CRITICAL: Double-check every letter for exact spelling. Do NOT replace letters, omit characters, or invent non-words. "
                f"POSITION: Centered strictly in the lower third of the image frame. "
                f"FONT STYLE: Clean, modern, bold white sans-serif typography. "
                f"COMPOSITION: Full-bleed edge-to-edge 4:5 vertical framing. "
                f"STRICT NEGATIVE PROMPT: Do NOT add borders, polaroid frames, photo mats, dates, timestamps, logos, or extra text."
            )
            contents = [image_prompt]
        else:
            image_prompt = (
                f"{chosen_style} themed around '{active_theme}'. "
                f"Slide {idx} of {num_slides} in a cohesive Instagram carousel sequence. "
                f"CHARACTER REFERENCE: Maintain the EXACT SAME man and woman from the reference image (identical faces, hair, and clothing), but CHANGE THEIR POSE, DISTANCE, AND ACTION to match the story progression. "
                f"VISUAL CONTINUITY: {subject_instruction} Maintain matching lighting, color palette, and art style. "
                f"{POSE_CONSTRAINT} "
                f"DYNAMIC SCENE PROGRESSION FOR SLIDE {idx}: Visually depict a NEW pose, interaction, or environment movement capturing the message: '{slide_text}'. "
                f"TYPOGRAPHY & TEXT OVERLAY: Overlay the exact text string: \"{slide_text}\" in clean, bold, white sans-serif typography. "
                f"CRITICAL: Double-check every letter for exact spelling. Do NOT replace letters, omit characters, or invent non-words. "
                f"POSITION: Centered strictly in the lower third of the image frame. "
                f"FONT STYLE: Clean, modern, bold white sans-serif typography. "
                f"UNIFORMITY: Ensure identical font family, size, placement, and alignment across every slide. "
                f"COMPOSITION: Full-bleed edge-to-edge 4:5 vertical framing. "
                f"STRICT NEGATIVE PROMPT: Do NOT add borders, polaroid frames, photo mats, dates, timestamps, logos, extra text, or typos."
            )
            contents = [first_slide_image, image_prompt]

        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="4:5",
                ),
            ),
        )

        slide_path_jpg = output_dir / f"slide_{idx}_of_{num_slides}.jpg"
        image_saved = False

        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    raw_image = Image.open(io.BytesIO(part.inline_data.data))
                    
                    if idx == 1:
                        first_slide_image = raw_image.copy()

                    # 1. Force exact 1080x1350 resolution
                    raw_image = raw_image.resize(
                        (TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS
                    )
                    
                    # 2. Save strictly as RGB JPEG
                    rgb_image = raw_image.convert("RGB")
                    rgb_image.save(slide_path_jpg, "JPEG", quality=95, optimize=True)
                    
                    image_saved = True
                    generated_image_paths.append(str(slide_path_jpg))
                    break

        if not image_saved:
            raise RuntimeError(f"Failed to generate slide {idx} for carousel.")

    return (
        generated_image_paths,
        slide_quotes,
        explanation,
        hashtags,
        music_recommendation,
    )