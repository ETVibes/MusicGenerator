import json
import os
import re
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError, ServerError

# Load .env from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def generate_vibe_and_text(selected_theme="Inspirational & Uplifting"):
  api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
  if not api_key:
    raise ValueError(
        "GEMINI_API_KEY or GOOGLE_API_KEY missing in your .env file."
    )

  client = genai.Client(api_key=api_key)

  theme_instructions = {
      "Inspirational & Uplifting": """
            THEME: Pure Inspiration & Uplifting Joy
            - Focus on joy, wonder, light, gratitude, inner peace, and the magic of everyday life.
            - ABSOLUTE BAN: Do NOT mention struggle, obstacles, pain, healing, dark times, or overcoming hardship.
        """,
      "Love & Romance": """
            THEME: Deep Love & Romance
            - Focus on warmth, deep connection, soulmates, romantic devotion, tenderness, and shared joy.
            - ABSOLUTE BAN: Do NOT mention heartbreak, hard times, fighting, or loss.
        """,
  }

  system_prompt = f"""
    You are a high-level creative scriptwriter for adult-focused motivational and romantic short-form videos (9:16 vertical format).

    {theme_instructions.get(selected_theme, theme_instructions["Inspirational & Uplifting"])}

    STRICT GUIDELINES:
    1. LENGTH: Maximum 2 to 3 concise, punchy parts/segments.
    2. TONE: Modern, warm, conversational, and poetic without being cheesy or overly dramatic.
    3. ZERO Hardship/Struggle language: Keep the lines entirely positive, uplifting, or romantic.

    YOUR PROCESS:
    1. Generate a short, beautiful quote (2 to 3 segments MAX) strictly following the assigned theme.
    2. Provide the quote split cleanly into the `sentences` array (must contain exactly 2 or 3 items).

    Output strictly valid raw JSON with this schema:
    {{
      "sub_genre": "Theme name",
      "inspiring_quote": "The full quote string",
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
      except (ServerError, APIError) as e:
        wait_time = (attempt + 1) * 3
        print(
            f"    [API Warning] {model_name} attempt {attempt + 1} failed:"
            f" {e}. Retrying in {wait_time}s..."
        )
        time.sleep(wait_time)

    if response:
      break

  if not response or not response.text:
    raise RuntimeError("All LLM attempts failed to return a response.")

  raw_text = response.text.strip()

  # Sanitize markdown formatting and extract JSON object payload
  if raw_text.startswith("```"):
    raw_text = re.sub(r"^```(?:json)?\n?", "", raw_text)
    raw_text = re.sub(r"\n?```$", "", raw_text)

  match = re.search(r"\{.*\}", raw_text, re.DOTALL)
  if match:
    raw_text = match.group(0)

  raw_text = re.sub(r"[\x00-\x1F\x7F]", " ", raw_text)

  try:
    return json.loads(raw_text)
  except json.JSONDecodeError:
    # Remove trailing commas before closing braces/brackets
    fixed_text = re.sub(r",(\s*[\}\]])", r"\1", raw_text)
    return json.loads(fixed_text, strict=False)