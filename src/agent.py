import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from text_generator import generate_vibe_and_text
from image_generator import generate_images_from_prompts

load_dotenv()


def create_unique_output_dir():
  """Creates a unique timestamped directory inside outputs/"""
  project_root = Path(__file__).resolve().parent.parent
  outputs_base = project_root / "outputs"

  # Unique folder name using date and time (e.g., run_20260803_175800)
  timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
  run_dir = outputs_base / f"run_{timestamp}"
  run_dir.mkdir(parents=True, exist_ok=True)

  return run_dir


def run_pipeline():
  # Create a dedicated unique folder for this run
  run_dir = create_unique_output_dir()
  images_dir = run_dir / "images"
  images_dir.mkdir(exist_ok=True)

  manifest_path = run_dir / "video_manifest.json"

  print(
      f"=== Starting New Pipeline Run ==="
      f"\nOutput Directory: {run_dir}\n"
  )

  # Step 1: Text & Prompt Generation via Gemini
  print("=== Step 1: Generating Text & Narrative Prompts (Gemini) ===")
  data = generate_vibe_and_text()

  print(f"Sub-Genre: {data.get('sub_genre')}")
  print(f"Quote: {data.get('inspiring_quote')}\n")

  # Save initial manifest in the run directory
  with open(manifest_path, "w") as f:
    json.dump(data, f, indent=2)

  # Step 2: Image Generation via gemini-2.5-flash-image
  print("=== Step 2: Generating Narrative Images (gemini-2.5-flash-image) ===")
  prompts = data.get("visual_narrative_prompts", [])

  if not prompts or len(prompts) != 4:
    raise ValueError(f"Expected 4 narrative prompts, but got {len(prompts)}.")

  # Generate and save images directly into the unique run directory
  image_paths = generate_images_from_prompts(prompts, output_dir=images_dir)

  # Update and finalize manifest with image paths
  data["scene_images"] = image_paths
  with open(manifest_path, "w") as f:
    json.dump(data, f, indent=2)

  print(f"\n=== Pipeline Complete! ===")
  print(f"Manifest saved to: {manifest_path}")
  print(f"Images saved to:  {images_dir}")


if __name__ == "__main__":
  run_pipeline()