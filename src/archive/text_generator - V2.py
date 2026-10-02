import json
import os
import random
import re
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError

# Load .env from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def generate_vibe_and_text():
  api_key = os.getenv("GEMINI_API_KEY")
  if not api_key:
    raise ValueError("GEMINI_API_KEY is missing in your .env file.")

  client = genai.Client(api_key=api_key)

  # Randomly pick ONE of the two themes for each generation run
  selected_theme = random.choice(["INSPIRATIONAL_UPLIFTING", "LOVE_AND_ROMANCE"])

  theme_instructions = {
      "INSPIRATIONAL_UPLIFTING": """
            THEME: Pure Inspiration & Uplifting Joy
            - Focus on joy, wonder, light, gratitude, inner peace, and the magic of everyday life.
            - ABSOLUTE BAN: Do NOT mention struggle, obstacles, pain, healing, dark times, or overcoming hardship. Focus purely on beauty and light.
            - EXAMPLE: "Some moments aren't meant to be captured on camera, just felt deeply in the quiet spaces of your heart."
        """,
      "LOVE_AND_ROMANCE": """
            THEME: Deep Love & Romance
            - Focus on warmth, deep connection, soulmates, romantic devotion, tenderness, and shared joy.
            - ABSOLUTE BAN: Do NOT mention heartbreak, hard times, fighting, or loss. Focus purely on affection and unconditional love.
            - EXAMPLE: "Loving you feels like coming home to a place I didn't know I was missing."
        """,
  }

  system_prompt = f"""
    You are a high-level creative scriptwriter for adult-focused motivational and romantic short-form videos (9:16 vertical format).

    {theme_instructions[selected_theme]}

    STRICT GUIDELINES:
    1. LENGTH: Maximum 2 to 3 concise, punchy parts/segments.
    2. TONE: Modern, warm, conversational, and poetic without being cheesy or overly dramatic.
    3. ZERO Hardship/Struggle language: Keep the lines entirely positive, uplifting, or romantic.

    YOUR PROCESS:
    1. Generate a short, beautiful quote (2 to 3 segments MAX) strictly following the assigned theme.
    2. Construct FOUR distinct visual prompts for AI image generation matching the mood and aesthetic.
    3. EVERY visual prompt MUST include: "9:16 vertical aspect ratio, portrait composition, cinematic 8k imagery."
    4. Provide the quote split cleanly into the `sentences` array (must contain exactly 2 or 3 items).

    Output strictly in JSON with this schema:
    {{
      "sub_genre": "Theme name (e.g., Pure Joy, Everyday Magic, Warm Affection, Soul Connections)",
      "inspiring_quote": "The full quote string",
      "visual_narrative_prompts": [
        "PROMPT 1 (0:00-0:08): Opening aesthetic scene. MUST INCLUDE '9:16 vertical aspect ratio, portrait composition, cinematic 8k imagery.'",
        "PROMPT 2 (0:08-0:17): Mid scene. MUST INCLUDE '9:16 vertical aspect ratio, portrait composition, cinematic 8k imagery.'",
        "PROMPT 3 (0:17-0:26): Emotional peak scene. MUST INCLUDE '9:16 vertical aspect ratio, portrait composition, cinematic 8k imagery.'",
        "PROMPT 4 (0:26-0:35): Closing peaceful scene. MUST INCLUDE '9:16 vertical aspect ratio, portrait composition, cinematic 8k imagery.'"
      ],
      "sentences": [
        "Part 1 string",
        "Part 2 string",
        "Part 3 string (optional, max 3 items total)"
      ]
    }}
    """

  # Primary and fallback models
  models_to_try = [
      "gemini-3.5-flash",
  ]
  response = None

  for model_name in models_to_try:
    # Try up to 3 times per model with exponential backoff
    for attempt in range(3):
      try:
        print(f"--> Calling {model_name} (Attempt {attempt + 1})...")
        response = client.models.generate_content(
            model=model_name,
            contents=system_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.8,
            ),
        )
        break  # Success! Break out of the attempt loop.
      except ServerError as e:
        if "503" in str(e) or "UNAVAILABLE" in str(e):
          wait_time = (attempt + 1) * 3
          print(
              f"    [503 Busy] {model_name} overloaded. Retrying in"
              f" {wait_time}s..."
          )
          time.sleep(wait_time)
        else:
          raise e

    if response:
      break  # Got a successful response, stop trying fallbacks

  if not response:
    raise RuntimeError(
        "All model attempts failed due to server demand spikes."
    )

  raw_text = response.text.strip()

  # Clean markdown block markers if present
  if raw_text.startswith("```"):
    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
    raw_text = re.sub(r"\s*```$", "", raw_text)

  # Extract the first valid JSON object payload
  match = re.search(r"\{.*\}", raw_text, re.DOTALL)
  if match:
    raw_text = match.group(0)

  return json.loads(raw_text)


if __name__ == "__main__":
  result = generate_vibe_and_text()
  print(json.dumps(result, indent=2))