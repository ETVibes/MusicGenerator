import json
import os
import re
import time
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load API key from root .env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_client() -> genai.Client:
    """Initializes standard Google AI Studio client using GEMINI_API_KEY."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY missing in .env file.")
    return genai.Client(api_key=api_key)


def generate_visual_prompts_from_quote(quote: str) -> List[str]:
    """Analyzes the quote story/energy and returns EXACTLY 4 distinct visual scene descriptions."""
    client = get_client()

    system_instruction = """
    You are an expert art director and visual storyteller for short video content (9:16 vertical format).
    Your job is to read an inspirational or thematic quote and convert its full narrative arc and energy into EXACTLY FOUR distinct, concrete visual scene descriptions.

    CRITICAL RULES:
    1. ALWAYS return EXACTLY 4 visual scene prompts capturing the progression/story of the quote.
    2. DO NOT use abstract metaphors. Focus on tangible subjects, lighting, environment, human gesture, and camera perspective.
    3. Output MUST be valid JSON: a list of exactly 4 strings.
    """

    user_prompt = f"""
    Full Quote: "{quote}"

    Generate 4 distinct visual scene prompts that tell the visual story matching the energy of this quote.
    Return JSON format: ["Scene 1 description", "Scene 2 description", "Scene 3 description", "Scene 4 description"]
    """

    models_to_try = ["gemini-3.5-flash", "gemini-2.0-flash"]
    response = None

    for model_name in models_to_try:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=f"{system_instruction}\n\n{user_prompt}",
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.7,
                    ),
                )
                if response and response.text:
                    break
            except Exception as e:
                wait_time = (attempt + 1) * 2
                print(f"    [Prompt Gen Warning] {model_name} attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)

        if response and response.text:
            break

    if not response or not response.text:
        print("Warning: Prompt generation models failed. Using quote fallback.")
        return [quote] * 4

    try:
        raw_text = response.text.strip()
        match = re.search(r"\[.*\]", raw_text, re.DOTALL)
        if match:
            raw_text = match.group(0)
        visual_descriptions = json.loads(raw_text, strict=False)
    except (json.JSONDecodeError, AttributeError):
        visual_descriptions = [quote] * 4

    if len(visual_descriptions) < 4:
        visual_descriptions += [quote] * (4 - len(visual_descriptions))

    return visual_descriptions[:4]


def format_final_image_prompt(scene_description: str, global_style: str = "") -> str:
    if not global_style:
        global_style = "Cinematic film photography, 35mm lens depth of field, soft natural lighting, warm color grading, 9:16 vertical framing, ultra-detailed, 8k resolution"
    
    negative_cues = "no text overlay, no watermarks, no UI buttons, no split screen, no blur"
    return f"Subject: {scene_description}. Aesthetic: {global_style}. Avoid: {negative_cues}."


def generate_images_for_quote(quote: str, sentences: List[str] = None) -> List[str]:
    """Generates 4 scene prompts matching the quote's story/vibe and creates 4 images via gemini-2.5-flash-image with retries."""
    print("Analyzing quote narrative for 4 visual scenes...")
    visual_descriptions = generate_visual_prompts_from_quote(quote)

    output_dir = Path("output/ui_generated_images")
    output_dir.mkdir(parents=True, exist_ok=True)

    client = get_client()
    image_paths = []

    for idx, desc in enumerate(visual_descriptions, 1):
        full_prompt = format_final_image_prompt(desc)
        print(f"\n--- Scene {idx} Prompt: {full_prompt}")

        image_saved = False
        # Up to 3 attempts per scene image
        for attempt in range(1, 4):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=f"Generate a high quality 9:16 vertical image: {full_prompt}",
                )

                save_path = output_dir / f"scene_{idx}.png"

                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data:
                            save_path.write_bytes(part.inline_data.data)
                            image_paths.append(str(save_path))
                            print(f"Successfully saved scene {idx} image to {save_path}")
                            image_saved = True
                            break

                if image_saved:
                    break

            except Exception as e:
                wait_time = attempt * 3
                print(f"    [Image Gen Warning] Scene {idx} attempt {attempt} failed: {e}.")
                if attempt < 3:
                    print(f"    Retrying scene {idx} in {wait_time}s...")
                    time.sleep(wait_time)

        if not image_saved:
            print(f"Error: Failed to generate scene {idx} image after 3 attempts.")

    return image_paths