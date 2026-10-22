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
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from moviepy import ImageClip, concatenate_videoclips
import smtplib

# Load environment variables
load_dotenv()

# Import generation and publishing functions
try:
    from src.Publish_IG_Post import publish_latest_single_image, publish_carousel_post, publish_latest_reel
    from src.prompt_config import get_random_theme
    from src.single_image_generator import generate_single_image_post
    from src.multi_slide_carousel_generator import generate_multi_slide_carousel
except ImportError as e:
    print(f"❌ Error importing project modules: {e}")
    sys.exit(1)
    
"""===============================================================================
    Automates sending an email with text and image prompts after post to IG is completed.

    Args:
        post_text and image_prompt_details

    Raises:
        
==============================================================================="""    
def send_post_notification(post_text, image_prompt_details):
  """Sends an email notification via Gmail using environment variables."""
  import smtplib
  from email.mime.multipart import MIMEMultipart
  from email.mime.text import MIMEText

  sender_email = os.getenv("SENDER_EMAIL")
  app_password = os.getenv("EMAIL_APP_PASSWORD")
  receiver_email = os.getenv("RECEIVER_EMAIL")

  if not sender_email or not app_password:
    print(
        "⚠️ [EMAIL WARNING] Missing SENDER_EMAIL or EMAIL_APP_PASSWORD in environment variables. Skipping email."
    )
    return

  msg = MIMEMultipart()
  msg["From"] = sender_email
  msg["To"] = receiver_email
  msg["Subject"] = "New Post Created - ETVibesMusicShortsGenerator"

  body = f"""Here are the details for the newly created post:

Text Content & Headline: 
{post_text}

Image Prompt(s): 
{image_prompt_details}
"""
  msg.attach(MIMEText(body, "plain"))

  try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
      server.starttls()
      server.login(sender_email, app_password)
      server.send_message(msg)
    print(f"  └─ 📧 Notification email sent successfully to {receiver_email}!")
  except Exception as e:
    print(f"  └─ ❌ Failed to send email notification: {e}")

"""===============================================================================
    Compiles a list of image file paths into a single MP4 video reel.

    Args:
        image_paths (list[str]): List of image paths to compile into video frames.
        duration_per_slide (float, optional): Display duration for each image in seconds. Defaults to 3.0.

    Returns:
        str: Absolute file path string of the generated reel MP4.
==============================================================================="""
def compile_images_to_reel(image_paths: list[str], duration_per_slide: float = 6.5) -> str:
    """Compiles a list of image file paths into a single MP4 video reel."""
    from pathlib import Path
    from moviepy import ImageClip, concatenate_videoclips

    reel_output_dir = Path("output") / "Reels"
    reel_output_dir.mkdir(parents=True, exist_ok=True)
    
    clips = [ImageClip(img).with_duration(duration_per_slide) for img in image_paths]
    final_video = concatenate_videoclips(clips, method="compose")
    
    output_video_path = reel_output_dir / "generated_reel.mp4"
    final_video.write_videofile(
        str(output_video_path), 
        fps=24, 
        codec="libx264", 
        audio=False, 
        preset="medium",
        logger=None
    )
    return str(output_video_path)
    
"""===============================================================================
    Automates the full content lifecycle: theme selection, media and caption generation
    via Gemini, and post submission to Instagram via the Buffer API.

    Args:
        theme (str, optional): Overrides theme choice. Defaults to a random theme if None.
        mode (str, optional): Post mode ("single" or "carousel"). If None, randomly picks one.
        post_type (str, optional): Target type ("post" or "reel"). Defaults to "post".
        num_slides (int, optional): Number of carousel slides if mode is "carousel". Defaults to 4.

    Raises:
        SystemExit: Exits script with code 1 if content generation or Buffer publishing fails.
==============================================================================="""
def run_auto_publish(theme: str = None, mode: str = "single", post_type: str = "post", num_slides: int = 4):

    # 0. Mode Selection (Randomize if not explicitly passed or if 'random' is requested)
    if not mode or mode.lower() == "random":
        mode = random.choice(["single", "carousel"])
        
    print("=" * 60)
    print(f"🚀 STARTING AUTOMATED INSTAGRAM PUBLISH JOB [{mode.upper()} MODE | TYPE: {post_type.upper()}]")
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
            image_paths, slide_quotes, explanation, hashtags, music_recommendation, image_prompts = (
                generate_multi_slide_carousel(theme=theme, num_slides=num_slides)
            )
            headline = " | ".join(slide_quotes)
            
            # Format multiple carousel prompts neatly for the email
            formatted_prompts = []
            for idx, p in enumerate(image_prompts, 1):
                formatted_prompts.append(f"--- Slide {idx} Prompt ---\n{p}")
            image_prompt_info = "\n\n".join(formatted_prompts)
            
            print("  └─ Carousel Generation Success!")
            print(f"  └─ Total Slides Saved: {len(image_paths)}")
            for idx, p in enumerate(image_paths, 1):
                print(f"     Slide {idx}: {p}")
        else:
            # Generate single image/panel and post text payload
            image_path, headline, explanation, hashtags, music_recommendation, image_prompt = (
                generate_single_image_post(theme)
            )
            image_paths = [image_path]
            image_prompt_info = image_prompt
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
        if post_type.lower() == "reel":
            print("  └─ Compiling generated images into video Reel format...")
            compile_images_to_reel(image_paths)
            res = publish_latest_reel(caption)
        elif mode == "carousel" and "publish_carousel_post" in globals():
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
            
            # Send email notification with the exact text and image prompts
            send_post_notification(caption, image_prompt_info)
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
        choices=["single", "carousel", "random"],
        default="single",
        help="Post format mode: single, carousel, or random",
    )
    parser.add_argument(
        "--type",
        type=str,
        choices=["post", "reel"],
        default="post",
        help="Instagram target type: post or reel",
    )
    parser.add_argument(
        "--slides",
        type=int,
        default=4,
        help="Number of slides for carousel mode",
    )

    args = parser.parse_args()
    run_auto_publish(theme=args.theme, mode=args.mode, post_type=args.type, num_slides=args.slides)