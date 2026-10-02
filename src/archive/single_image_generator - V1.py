from datetime import datetime
from pathlib import Path
from google import genai
from google.genai import types


def generate_single_image_post(theme: str) -> tuple[str, str]:
    client = genai.Client()

    # 1. Generate text quote using gemini-3.6-flash
    text_prompt = (
        f"Write a single short, impactful, and inspiring sentence (4-6 words max) "
        f"suitable for an Instagram quote post with the theme '{theme}'. "
        f"Do not use quotation marks or punctuation at the end."
    )
    sentence_response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=text_prompt,
    )
    short_sentence = sentence_response.text.strip().replace('"', "")

    # 2. Direct Gemini Image Generation with animated style and man/woman interaction
    image_prompt = (
        f"An animated digital illustration aesthetic picture inspired by the theme '{theme}'. "
        f"It features a man and a woman interacting with each other in a scene that visually represents and captures the emotional meaning of the sentence: '{short_sentence}'. "
        f"The text '{short_sentence}' is overlayed clearly in elegant, centered typography "
        f"with high contrast and perfect legibility in the center of the image."
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=image_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio="9:16",
            ),
        ),
    )

    # Save to output/Single_Image with a unique timestamp
    output_dir = Path("output") / "Single_Image"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_path = output_dir / f"single_image_post_{timestamp}.png"

    # Save generated image bytes directly
    image_saved = False
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                output_path.write_bytes(part.inline_data.data)
                image_saved = True
                break

    if not image_saved:
        raise RuntimeError("Gemini failed to return an image in the response.")

    return str(output_path), short_sentence