import json
import os
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


def generate_vibe_and_text(selected_theme="INSPIRATIONAL_UPLIFTING"):
  api_key = os.getenv("GEMINI_API_KEY")
  if not api_key:
    raise ValueError("GEMINI_API_KEY is missing in your .env file.")

  client = genai.Client(api_key=api_key)

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

    {theme_instructions.get(selected_theme, theme_instructions["INSPIRATIONAL_UPLIFTING"])}

    STRICT GUIDELINES:
    1. LENGTH: Maximum 2 to 3 concise, punchy parts/segments.
    2. TONE: Modern, warm, conversational, and poetic without being cheesy or overly dramatic.
    3. ZERO Hardship/Struggle language: Keep the lines entirely positive, uplifting, or romantic.

    YOUR PROCESS:
    1. Generate a short, beautiful quote (2 to 3 segments MAX) strictly following the assigned theme.
    2. Construct FOUR distinct visual prompts for AI image generation matching the mood and aesthetic.
    3. EVERY visual prompt MUST include: "9:16 vertical aspect ratio, portrait composition, cinematic 8k imagery."
    4. Provide the quote split cleanly into the `sentences` array (must contain exactly 2 or 3 items).

    Output strictly valid raw JSON with this schema:
    {{
      "sub_genre": "Theme name",
      "inspiring_quote": "The full quote string",
      "visual_narrative_prompts": [
        "PROMPT 1...",
        "PROMPT 2...",
        "PROMPT 3...",
        "PROMPT 4..."
      ],
      "sentences": [
        "Part 1 string",
        "Part 2 string"
      ]
    }}
    """

  models_to_try = [
      "gemini-3.5-flash",
  ]
  response = None

  for model_name in models_to_try:
    for attempt in range(3):
      try:
        print(
            f"--> Calling {model_name} for theme '{selected_theme}' (Attempt"
            f" {attempt + 1})..."
        )
        response = client.models.generate_content(
            model=model_name,
            contents=system_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.8,
            ),
        )
        break
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
      break

  if not response:
    raise RuntimeError(
        "All model attempts failed due to server demand spikes."
    )

  raw_text = response.text.strip()

  # 1. Strip markdown block backticks if returned
  if raw_text.startswith("```"):
    raw_text = re.sub(r"^```(?:json)?\n?", "", raw_text)
    raw_text = re.sub(r"\n?```$", "", raw_text)

  # 2. Extract valid JSON object
  match = re.search(r"\{.*\}", raw_text, re.DOTALL)
  if match:
    raw_text = match.group(0)

  # 3. Clean control characters (like raw unescaped newlines inside strings)
  raw_text = re.sub(r"[\x00-\x1F\x7F]", " ", raw_text)

  try:
    return json.loads(raw_text)
  except json.JSONDecodeError:
    return json.loads(raw_text, strict=False)