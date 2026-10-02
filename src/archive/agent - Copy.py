import json
import os
from dotenv import load_dotenv

from suno_generator import generate_suno_audio
from text_generator import generate_vibe_and_text

# Load environment variables from .env file
load_dotenv()


def run_pipeline():
  print("=== Step 1: Generating Creative Assets ===")
  data = generate_vibe_and_text()

  sub_genre = data["sub_genre"]
  suno_prompt = data["suno_prompt"]
  sentences = data["sentences"]

  print(f"Sub-Genre: {sub_genre}")
  print(f"Suno Prompt: {suno_prompt}")

  print("\n=== Step 2: Generating Audio via Suno API ===")
  # Clean title string for API submission
  clean_title = (
    f"ETVibes_{sub_genre}".replace(" ", "_")
    .replace("&", "and")
    .replace("-", "_")
)
  audio_path = generate_suno_audio(suno_prompt, clean_title)

  print("\n=== Step 3: Saving Manifest for Video Editing ===")
  timestamps = ["0:00 - 0:08", "0:08 - 0:17", "0:17 - 0:26", "0:26 - 0:35"]
  manifest = {
      "sub_genre": sub_genre,
      "audio_file": audio_path,
      "suno_prompt": suno_prompt,
      "text_timeline": [
          {"timestamp": timestamps[i], "text": sentences[i]}
          for i in range(len(sentences))
      ],
  }

  manifest_path = os.path.join("outputs", "video_manifest.json")
  with open(manifest_path, "w") as f:
    json.dump(manifest, f, indent=2)

  print(f"Pipeline complete! Output saved to '{manifest_path}'.")


if __name__ == "__main__":
  run_pipeline()