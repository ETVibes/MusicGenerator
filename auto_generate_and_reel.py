"""===============================================================================
Module: automation_pipeline.py
Description: Automated CLI pipeline for generating and publishing Instagram posts
             (single-image or multi-slide carousels) using Gemini generative AI
             models, local file management, and the Buffer GraphQL API.
==============================================================================="""
import argparse
import os
import sys
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import generation and publishing functions
try:
    from src.Publish_IG_Post import publish_latest_single_image, publish_carousel_post
    from src.prompt_config import get_random_theme
    from src.single_image_generator import generate_single_image_post
    from src.multi_slide_carousel_generator import generate_multi_slide_carousel
except ImportError as e:
    print(f"❌ Error importing project modules: {e}")
    sys.exit(1)

"""===============================================================================
    Automates the full content lifecycle: theme selection, media and caption generation
    via Gemini, and post submission to Instagram via the Buffer API.

    Args:
        theme (str, optional): Overrides theme choice. Defaults to a random theme if None.
        mode (str, optional): Post mode ("single" or "carousel"). If None, randomly picks one.
        num_slides (int, optional): Number of carousel slides if mode is "carousel". Defaults to 4.

    Raises:
        SystemExit: Exits script with code 1 if content generation or Buffer publishing fails.
==============================================================================="""
def run_auto_publish(theme: str = None, mode: str = "single", num_slides: int = 4):

    # 0. Mode Selection (Randomize if not explicitly passed)
    if not mode:
        mode = random.choice(["single", "carousel"])
        
    print("=" * 60)
    print(f"🚀 STARTING AUTOMATED INSTAGRAM PUBLISH JOB [{mode.upper()} MODE]")
    print("=" * 60)

    # 1. Select Theme
    if not theme:
        theme = get_random_theme()
    print(f"\n[STEP 1/3] Selected Theme: '{theme}'")

    # 2. Generate Content via Gemini
    print(f"[STEP 2/3] Generating {mode} post content via Gemini...")
    try:
        if mode == "carousel":
            # Generate multi-slide images and narrative text payload
            image_paths, slide_quotes, explanation, hashtags, music_recommendation = (
                generate_multi_slide_carousel(theme=theme, num_slides=num_slides)
            )
            headline = " | ".join(slide_quotes)
            print("  └─ Carousel Generation Success!")
            print(f"  └─ Total Slides Saved: {len(image_paths)}")
            for idx, p in enumerate(image_paths, 1):
                print(f"     Slide {idx}: {p}")
        else:
            # Generate single image/panel and post text payload
            image_path, headline, explanation, hashtags, music_recommendation = (
                generate_single_image_post(theme)
            )
            image_paths = [image_path]
            print("  └─ Single Image Generation Success!")
            print(f"  └─ Quote Embedded: \"{headline}\"")
            print(f"  └─ Image File Saved: {image_path}")

        print(f"  └─ Recommended Audio: {music_recommendation}")

    except Exception as e:
        print(f"❌ [STEP 2 FAILED] Generation failed: {e}")
        sys.exit(1)

    # 3. Upload & Publish to Instagram
    print("\n[STEP 3/3] Publishing to Instagram via Buffer API...")

    caption = f"{headline}\n\n{explanation}\n\n🎵 Suggested Audio: {music_recommendation}\n\n✨ {hashtags}"

    try:
        if mode == "carousel" and "publish_carousel_post" in globals():
            res = publish_carousel_post(image_paths, caption)
        else:
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
    parser = argparse.ArgumentParser(description="Auto generate and post content to Instagram.")
    parser.add_argument("--theme", type=str, default=None, help="Theme for the post")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["single", "carousel"],
        default="single",
        help="Post format mode: single or carousel",
    )
    parser.add_argument(
        "--slides",
        type=int,
        default=4,
        help="Number of slides for carousel mode",
    )

    args = parser.parse_args()
    run_auto_publish(theme=args.theme, mode=args.mode, num_slides=args.slides)