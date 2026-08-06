import json
import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load .env from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def generate_vibe_and_text():
  api_key = os.getenv("GEMINI_API_KEY")
  if not api_key:
    raise ValueError("GEMINI_API_KEY is missing in your .env file.")

  client = genai.Client(api_key=api_key)

  system_prompt = """
    You are a creative content strategist for high-performing relaxation videos.
    Select a random high-performing relaxation sub-genre or instrument combination (e.g., Tibetan Singing Bowls, Native American Flute, Soft Piano & Rain, Sitar Meditation, Ambient Harp, etc.).
    
    Output strictly in JSON with the following schema:
    {
      "sub_genre": "Name of subgenre",
      "suno_prompt": "Tag-based music prompt for Suno under 200 chars (~50-60bpm, atmospheric, pure instrumental, no drums)",
      "sentences": [
        "Sentence 1 (0:00 - 0:08)",
        "Sentence 2 (0:08 - 0:17)",
        "Sentence 3 (0:17 - 0:26)",
        "Sentence 4 (0:26 - 0:35)"
      ]
    }
    """

  # Set model string to gemini-2.0-flash
  response = client.models.generate_content(
      model="gemini-3.5-flash",
      contents=system_prompt,
      config=types.GenerateContentConfig(
          response_mime_type="application/json",
      ),
  )

  return json.loads(response.text)