"""===============================================================================
Module: single_image_generator.py
Description: Generates standalone Instagram image posts (single frame or multi-panel
             stacked layouts) with optimized curiosity pacing and clean visual framing.
==============================================================================="""
from datetime import datetime
import io
from pathlib import Path
import random
from google import genai
from google.genai import types
from PIL import Image

from .prompt_config import (
    POSE_CONSTRAINT,
    TARGET_HEIGHT,
    TARGET_WIDTH,
    get_style_and_modifier_for_theme,
    get_random_theme,
    get_subject_and_instructions,
)

def generate_single_image_post(
    theme: str = None, force_panels: int = None
) -> tuple[str, str, str, str, str, str]:
    """Generates an Instagram post image, quote, explanation, hashtags, and music recommendation."""
    client = genai.Client()

    active_theme = theme if theme else get_random_theme()
    num_panels = (
        force_panels
        if force_panels in [1, 2, 3]
        else random.choice([1, 2, 3])
    )
    
    character_desc, subject_instruction = get_subject_and_instructions(active_theme)
    chosen_style, emotional_modifier = get_style_and_modifier_for_theme(active_theme)

    if num_panels == 1:
        text_prompt = (
            f"Write an Instagram post caption package for the theme '{active_theme}'.\n"
            f"1. A single complete, punchy statement or hook (5-8 words) that delivers a clear, whole thought without feeling cut off.\n"
            f"2. A 1-2 sentence clear, grounded explanation that reinforces the main point.\n"
            f"3. 6 to 9 relevant, high-engagement Instagram hashtags tailored specifically to '{active_theme}' (always include #thisisdailywhisper).\n"
            f"4. A suggested song title and viral audio genre keyword available on Instagram Audio.\n\n"
            f"Format strictly as:\n"
            f"QUOTE: <your complete quote without quotation marks>\n"
            f"EXPLANATION: <your explanation>\n"
            f"HASHTAGS: <your hashtags separated by spaces>\n"
            f"MUSIC: <song name - artist name | genre mood>"
        )
        sentence_response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=text_prompt,
        )
        raw_text = sentence_response.text.strip()
        
        short_sentence = ""
        explanation = ""
        hashtags = "#thisisdailywhisper #inspiration #motivation"
        music_recommendation = ""

        for line in raw_text.splitlines():
            clean_line = line.replace("*", "").strip()
            if clean_line.startswith("QUOTE:"):
                short_sentence = clean_line.replace("QUOTE:", "", 1).strip().replace('"', "")
            elif clean_line.startswith("EXPLANATION:"):
                explanation = clean_line.replace("EXPLANATION:", "", 1).strip()
            elif clean_line.startswith("HASHTAGS:"):
                hashtags = clean_line.replace("HASHTAGS:", "", 1).strip()
            elif clean_line.startswith("MUSIC:"):
                music_recommendation = clean_line.replace("MUSIC:", "", 1).strip()

        if not short_sentence:
            short_sentence = raw_text.splitlines()[0].replace('"', "")

        image_prompt = (
            f"{chosen_style}. Theme: {active_theme}. "
            f"Subject: {character_desc}, {emotional_modifier}. "
            f"Composition: High contrast vertical 1080x1350 canvas with generous top and bottom safety margins for UI overlays. "
            f"{POSE_CONSTRAINT} "
            f"Overlay typography: Stark white, high-contrast bold sans-serif text reading '{short_sentence}' centered cleanly."
        )

    else:
        format_example = " | ".join([f"<complete panel {i+1}>" for i in range(num_panels)])
        arc_rule = (
            "Panel 1 states a clear setup or truth; Panel 2 delivers a complete shift or payoff so the full message lands cleanly."
            if num_panels == 2
            else "Panel 1 sets up the situation, Panel 2 shows the turning point, and Panel 3 delivers a complete, satisfying payoff."
        )
        text_prompt = (
            f"Write an Instagram multi-panel story post for the theme '{active_theme}'.\n"
            f"1. A {num_panels}-part sequence separated strictly by '|'. Each segment must be 5-8 words, grammatically complete on its own, and free of trailing ellipses or cut-off fragments. {arc_rule}\n"
            f"2. A 1-2 sentence clear, grounded explanation tying the full sequence together.\n"
            f"3. 5 relevant, high-engagement Instagram hashtags tailored specifically to '{active_theme}' (always include #thisisdailywhisper).\n"
            f"4. A suggested song title and viral audio genre keyword available on Instagram Audio.\n\n"
            f"Format strictly as:\n"
            f"QUOTE: {format_example}\n"
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
            clean_line = line.replace("*", "").strip()
            if clean_line.startswith("QUOTE:"):
                quote_raw = clean_line.replace("QUOTE:", "", 1).strip().replace('"', "")
            elif clean_line.startswith("EXPLANATION:"):
                explanation = clean_line.replace("EXPLANATION:", "", 1).strip()
            elif clean_line.startswith("HASHTAGS:"):
                hashtags = clean_line.replace("HASHTAGS:", "", 1).strip()
            elif clean_line.startswith("MUSIC:"):
                music_recommendation = clean_line.replace("MUSIC:", "", 1).strip()

        parts = [p.strip() for p in quote_raw.split("|") if p.strip()]

        if len(parts) > num_panels:
            parts = parts[:num_panels]
        elif len(parts) < num_panels:
            raise ValueError(f"Expected {num_panels} parts, got {len(parts)}: {quote_raw!r}")

        short_sentence = " / ".join(parts)

        panel_descriptions = " - ".join([f"Panel {idx}: '{part}'" for idx, part in enumerate(parts, 1)])

        image_prompt = (
            f"{chosen_style}. {num_panels}-row vertically stacked layout on a high-contrast 1080x1350 canvas. Theme: {active_theme}. "
            f"Subject: {character_desc}, {emotional_modifier}. "
            f"Panels with complete thoughts: {panel_descriptions}. "
            f"{POSE_CONSTRAINT} "
            f"{subject_instruction} Clean horizontal panel borders, distinct framing per row, and high-contrast bold typography for max mobile readability."
        )

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=image_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio="4:5",
            ),
        ),
    )

    output_dir = Path("output") / "Single_Image"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_path = output_dir / f"single_image_post_{timestamp}.png"

    image_saved = False
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                raw_image = Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
                if raw_image.size != (TARGET_WIDTH, TARGET_HEIGHT):
                    raw_image = raw_image.resize(
                        (TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS
                    )
                raw_image.save(output_path, "PNG")
                image_saved = True
                break

    if not image_saved:
        raise RuntimeError("Gemini failed to return an image in the response.")

    return str(output_path), short_sentence, explanation, hashtags, music_recommendation, image_prompt