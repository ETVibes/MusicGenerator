"""===============================================================================
Module: multi_slide_carousel_generator.py
Description: Generates multi-slide Instagram carousel posts matching high-contrast
             visual quality, curiosity-loop pacing, and character consistency.
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

def generate_multi_slide_carousel(
    theme: str = None, num_slides: int = 4
) -> tuple[list[str], list[str], str, str, str, list[str]]:
    """Generates an Instagram multi-slide carousel post with visual continuity across separate images."""
    client = genai.Client()
    active_theme = theme if theme else get_random_theme()
    chosen_style = get_random_style()
    character_desc, subject_instruction = get_subject_and_instructions(active_theme)
    emotional_modifier = get_emotional_visual_modifier()

    # 1. High-Engagement Curiosity-Loop Script Generation for Carousel
    text_prompt = (
        f"Write an Instagram multi-slide curiosity-loop carousel post caption package for the theme '{active_theme}'.\n"
        f"1. Generate {num_slides} high-impact narrative sentences (4-7 words per slide) separated strictly by '|'. "
        f"Each slide must build an open psychological loop or cliffhanger forcing the user to swipe to the next slide.\n"
        f"2. A 2-3 sentence inspiring overall caption explanation reflecting deeply on the narrative.\n"
        f"3. 6 to 9 relevant, high-engagement Instagram hashtags tailored specifically to '{active_theme}' (always include #thisisdailywhisper).\n"
        f"4. A suggested song title and viral audio genre keyword available on Instagram Audio.\n\n"
        f"Format strictly as:\n"
        f"QUOTE: <slide 1 quote | slide 2 quote | slide 3 quote ...>\n"
        f"EXPLANATION: <your explanation>\n"
        f"HASHTAGS: <your hashtags separated by spaces>\n"
        f"MUSIC: <song name - artist name | genre mood>"
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
    generated_image_prompts = []
    first_slide_image = None

    # 2. Sequential Slide Rendering with High-Contrast Prompt Styling
    for idx, slide_text in enumerate(slide_quotes, 1):
        if idx == 1:
            image_prompt = (
                f"{chosen_style}. Theme: {active_theme}. "
                f"Slide {idx} of {num_slides} in a high-engagement Instagram carousel sequence. "
                f"Subject: {character_desc}, {emotional_modifier}. "
                f"Consistency: {subject_instruction} "
                f"Composition: High contrast vertical 1080x1350 canvas with generous top and bottom safety margins for UI overlays. "
                f"{POSE_CONSTRAINT} "
                f"Overlay typography: Stark white, high-contrast bold sans-serif text reading '{slide_text}' centered cleanly."
            )
            contents = [image_prompt]
        else:
            image_prompt = (
                f"{chosen_style}. Theme: {active_theme}. "
                f"Slide {idx} of {num_slides} in a high-engagement Instagram carousel sequence. "
                f"Subject: Maintain the exact same main subject from the reference image with consistent facial features, hair, and apparel across slides. "
                f"Consistency: {subject_instruction} "
                f"Composition: High contrast vertical 1080x1350 canvas with generous top and bottom safety margins for UI overlays. "
                f"{POSE_CONSTRAINT} "
                f"Overlay typography: Stark white, high-contrast bold sans-serif text reading '{slide_text}' centered cleanly."
            )
            contents = [first_slide_image, image_prompt]
            
        generated_image_prompts.append(image_prompt)    

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

                    raw_image = raw_image.resize(
                        (TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS
                    )
                    
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
        generated_image_prompts,
    )