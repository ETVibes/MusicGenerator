import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)


def generate_images_from_prompts(prompts, output_dir):
  """Generates 4 vertical 9:16 images using Google's image generation."""
  api_key = os.getenv("GEMINI_API_KEY")
  if not api_key:
    raise ValueError("GEMINI_API_KEY is missing in your .env file.")

  client = genai.Client(api_key=api_key)
  output_dir = Path(output_dir)
  output_dir.mkdir(parents=True, exist_ok=True)

  image_paths = []

  for i, prompt in enumerate(prompts):
    local_filename = output_dir / f"scene_{i + 1:02d}.png"
    print(f"--> Generating Scene {i + 1}/4 with Google Image Gen...")

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio="9:16",  # Native vertical aspect ratio
            ),
        ),
    )

    # Save the generated image part
    saved = False
    for part in response.parts:
      if part.inline_data:
        image = part.as_image()
        image.save(local_filename)
        saved = True
        break

    if saved:
      image_paths.append(str(local_filename))
    else:
      raise RuntimeError(f"Failed to extract image for scene {i + 1}")

  return image_paths