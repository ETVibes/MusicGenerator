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

    # 1. Fully dynamic, theme-agnostic text prompt generation
    text_prompt = (
        f"You are part of the core target audience who has personally experienced the emotions, struggles, desires, and inner conflicts surrounding '{active_theme}'. "
        f"You don't simply care about this theme — you have lived it, felt its impact, questioned yourself because of it, and carried thoughts you rarely express out loud. "
        f"Think about the quiet moments of vulnerability, the memories that still stir emotions, the fears people hide behind a smile, the things left unsaid, and the realizations that can suddenly change how someone sees their life. "
        f"You scroll Instagram searching for something that makes you stop and think, 'That's exactly how I feel, but I've never been able to put it into words.' "
        f"Connect with the audience through deeply personal, emotionally honest, and universally relatable experiences that awaken memories, create an immediate feeling of being understood, and inspire genuine reflection, emotional connection, and meaningful insights.\n\n"
        f"1. Generate {num_slides} short, powerful hook sentences (3-6 words max per slide) separated strictly by '|'. "
        f"Each slide must capture an authentic thought, feeling, or realization that stops your thumb mid-scroll and makes you want to swipe.\n"
        f"2. CRITICAL SPELLING RULE: Use extremely simple, clean, and common English words. Avoid complex double-consonant spelling words prone to image generation typos (such as 'trapped' or 'shattered'); instead, use clean, foolproof wording.\n"
        f"3. A 2-3 sentence inspiring overall caption explanation reflecting deeply on the carousel narrative from this audience perspective.\n"
        f"4. 6 to 9 relevant, high-engagement Instagram hashtags tailored specifically to '{active_theme}' (always include #thisisdailywhisper).\n"
        f"5. A suggested song title and viral audio genre keyword available on Instagram Audio that matches the emotional vibe.\n\n"
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
    hashtags = "#thisisdailywhisper"
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
                f"You are part of the target audience who has personally lived through the emotions of '{active_theme}'. "
                f"Design a deeply authentic, thumb-stopping, high-contrast vertical 1080x1350 visual composition for Slide {idx} of {num_slides} with slide text: '{slide_text}' "
                f"that visually captures a quiet moment of vulnerability and personal realization. "
                f"Subject: {character_desc}, {emotional_modifier}. "
                f"Consistency: {subject_instruction} "
                f"Composition rules: Generous top and bottom safety margins for Instagram UI overlays. "
                f"{POSE_CONSTRAINT} "
                f"Overlay typography: Stark white, high-contrast bold sans-serif text reading '{slide_text}' centered cleanly. "
                f"CRITICAL SPELLING RULE: Double-check letter accuracy to prevent rendering typos."
            )
            contents = [image_prompt]
        else:
            image_prompt = (
                f"You are part of the target audience who has personally lived through the emotions of '{active_theme}'. "
                f"Design the next visual frame for Slide {idx} of {num_slides} with slide text: '{slide_text}', "
                f"maintaining visual continuity with the reference slide image (keeping the exact same main subject with consistent facial features, hair, and apparel), "
                f"while shifting the pose, framing, and environment subtly to reflect an emotional turning point or inner breakthrough. "
                f"Composition rules: High-contrast vertical 1080x1350 canvas with safe margins. "
                f"{POSE_CONSTRAINT} "
                f"Overlay typography: Stark white, high-contrast bold sans-serif text reading '{slide_text}' centered cleanly. "
                f"CRITICAL SPELLING RULE: Double-check letter accuracy to prevent rendering typos."
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