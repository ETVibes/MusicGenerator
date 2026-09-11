import os
import sys
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import generation and publishing functions
try:
    from src.single_image_generator import generate_single_image_post
    from src.Publish_IG_Post import publish_latest_single_image
except ImportError as e:
    print(f"❌ Error importing project modules: {e}")
    sys.exit(1)


THEMES = ["Inspirational & Uplifting", "Love & Romance"]


def run_auto_publish(theme: str = None):
    """Automates image generation and Instagram publishing with detailed CLI logs."""
    print("=" * 60)
    print("🚀 STARTING AUTOMATED SINGLE IMAGE GENERATION & PUBLISH JOB")
    print("=" * 60)

    # 1. Select Theme
    if not theme:
        theme = random.choice(THEMES)
    print(f"\n[STEP 1/3] Selected Theme: '{theme}'")

    # 2. Generate Image & Text
    print("[STEP 2/3] Generating image and overlay quote via Gemini...")
    try:
        image_path, sentence = generate_single_image_post(theme)
        print(f"  └─ Success!")
        print(f"  └─ Quote Embedded: \"{sentence}\"")
        print(f"  └─ Image File Saved: {image_path}")
    except Exception as e:
        print(f"❌ [STEP 2 FAILED] Image generation failed: {e}")
        sys.exit(1)

    # 3. Upload & Publish to Instagram
    print("\n[STEP 3/3] Publishing to Instagram via Buffer API...")
    caption = f"{sentence}\n\n✨ #dailywhisper #inspiration #motivation"

    try:
        res = publish_latest_single_image(caption)
        post_data = res.get("data", {}).get("createPost", {})

        if "post" in post_data:
            post_id = post_data["post"].get("id", "N/A")
            status = post_data["post"].get("status", "N/A")
            print("=" * 60)
            print("🎉 PUBLISH SUCCESSFUL!")
            print(f"  └─ Buffer Post ID: {post_id}")
            print(f"  └─ Status: {status}")
            print("=" * 60)
        else:
            err_msg = res.get("errors", [{}])[0].get("message", str(res))
            print(f"❌ [STEP 3 FAILED] Buffer API Error: {err_msg}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ [STEP 3 FAILED] Exception during publish: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Optionally accept theme as command line argument (e.g. python auto_generate_and_post.py "Love & Romance")
    selected_theme = sys.argv[1] if len(sys.argv) > 1 else None
    run_auto_publish(selected_theme)