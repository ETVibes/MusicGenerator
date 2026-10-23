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
    get_random_style,
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
    chosen_style = get_random_style()
    character_desc, subject_instruction = get_subject_and_instructions(active_theme)
    chosen_style, emotional_modifier = get_style_and_modifier_for_theme(active_theme)

    if num_panels == 1:
        text_prompt = (
            f"Write an Instagram post caption package for the theme '{active_theme}'.\n"
            f"1. A single short, high-impact curiosity hook sentence (4-6 words max).\n"
            f"2. A 2-3 sentence inspiring explanation reflecting deeply on the sentence.\n"
            f"3. 6 to 9 relevant, high-engagement Instagram hashtags tailored specifically to '{active_theme}' (always include #thisisdailywhisper).\n"
            f"4. A suggested song title and viral audio genre keyword available on Instagram Audio.\n\n"
            f"Format strictly as:\n"
            f"QUOTE: <your quote without quotation marks>\n"
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
            if line.startswith("QUOTE:"):
                short_sentence = line.replace("QUOTE:", "").strip().replace('"', "")
            elif line.startswith("EXPLANATION:"):
                explanation = line.replace("EXPLANATION:", "").strip()
            elif line.startswith("HASHTAGS:"):
                hashtags = line.replace("HASHTAGS:", "").strip()
            elif line.startswith("MUSIC:"):
                music_recommendation = line.replace("MUSIC:", "").strip()

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
        text_prompt = (
            f"Write an Instagram multi-panel curiosity-loop story post for the theme '{active_theme}'.\n"
            f"1. A short {num_panels}-part narrative sequence where each part builds an open psychological loop or cliffhanger, separated strictly by '|'.\n"
            f"2. A 2-3 sentence inspiring explanation reflecting deeply on the story.\n"
            f"3. 5 relevant, high-engagement Instagram hashtags tailored specifically to '{active_theme}' (always include #thisisdailywhisper).\n"
            f"4. A suggested song title and viral audio genre keyword available on Instagram Audio.\n\n"
            f"Format strictly as:\n"
            f"QUOTE: <segment 1 | segment 2 | segment 3>\n"
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

        parts = [p.strip() for p in quote_raw.split("|") if p.strip()]

        if len(parts) != num_panels:
            parts = [f"Part {i+1}" for i in range(num_panels)]

        short_sentence = " ".join(parts)

        panel_descriptions = " - ".join([f"Panel {idx}: '{part}'" for idx, part in enumerate(parts, 1)])

        image_prompt = (
            f"{chosen_style}. {num_panels}-row vertically stacked layout on a high-contrast 1080x1350 canvas. Theme: {active_theme}. "
            f"Subject: {character_desc}, {emotional_modifier}. "
            f"Narrative panels with open loops: {panel_descriptions}. "
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