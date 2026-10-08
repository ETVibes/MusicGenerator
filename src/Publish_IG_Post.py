"""===============================================================================
Module: Publish_IG_Post.py
Description: Automated publishing bridge for Instagram posts. Handles discovering
             locally generated images (single or carousel), uploading assets to
             Cloudinary for temporary hosting, verifying CDN availability, and
             dispatching payloads to Buffer's GraphQL API.
==============================================================================="""
import glob
import logging
import os
from pathlib import Path
import re
import time
import requests
from dotenv import load_dotenv

# Updated imports for MoviePy v2.x compatibility
from moviepy import (
    VideoFileClip,
    AudioFileClip,
    TextClip,
    CompositeVideoClip,
    ImageClip,
    concatenate_videoclips,
    vfx
)

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

BUFFER_API_KEY = os.getenv("BUFFER_API_KEY")
BUFFER_CHANNEL_ID = os.getenv("BUFFER_INSTAGRAM_CHANNEL_ID")

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# Dynamically set IMAGE_DIR relative to project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
SINGLE_IMAGE_DIR = BASE_DIR / "output" / "Single_Image"
CAROUSEL_DIR = BASE_DIR / "output" / "Carousel_Posts"
REELS_OUTPUT_DIR = BASE_DIR / "output" / "Reels"


def sanitize_caption_for_instagram(caption: str, max_hashtags: int = 5) -> str:
    """
    Ensures the caption contains no more than 5 hashtags to satisfy Buffer
    and Instagram Graph API restrictions.
    """
    hashtags = re.findall(r'#\w+', caption)
    if len(hashtags) > max_hashtags:
        logger.warning(
            f"Found {len(hashtags)} hashtags in caption. "
            f"Trimming to {max_hashtags} to comply with Instagram API limits."
        )
        excess_tags = hashtags[max_hashtags:]
        for tag in excess_tags:
            caption = re.sub(r'\b' + re.escape(tag) + r'\b', '', caption)
        caption = re.sub(r' +', ' ', caption).strip()
    return caption


def get_latest_image(folder_path: Path) -> str:
    """Finds the most recently modified image (.jpg, .jpeg, .png) in the specified directory."""
    folder_path = Path(folder_path)
    extensions = ("*.jpg", "*.jpeg", "*.png")
    files = []
    for ext in extensions:
        files.extend(glob.glob(str(folder_path / ext)))

    if not files:
        logger.error(f"No image files found in {folder_path}")
        raise FileNotFoundError(f"No image files found in {folder_path}")

    latest_file = max(files, key=os.path.getmtime)
    logger.info(f"Selected latest single image: {latest_file}")
    return latest_file


def convert_latest_carousel_to_mp4(
    base_carousel_dir: Path = CAROUSEL_DIR, 
    slide_duration: float = 3.0, 
    fps: int = 30
) -> str:
    """Finds the latest carousel folder and converts all slide images into a single MP4 Reel file."""
    base_carousel_dir = Path(base_carousel_dir)
    if not base_carousel_dir.exists():
        logger.error(f"Carousel directory does not exist: {base_carousel_dir}")
        raise FileNotFoundError(f"Carousel directory does not exist: {base_carousel_dir}")

    subdirs = [p for p in base_carousel_dir.iterdir() if p.is_dir()]
    if not subdirs:
        logger.error(f"No carousel folders found in {base_carousel_dir}")
        raise FileNotFoundError(f"No carousel folders found in {base_carousel_dir}")

    latest_folder = max(subdirs, key=os.path.getmtime)
    logger.info(f"Selected latest carousel folder: {latest_folder}")

    extensions = ("*.jpg", "*.jpeg", "*.png")
    image_files = []
    for ext in extensions:
        image_files.extend(glob.glob(str(latest_folder / ext)))

    if not image_files:
        logger.error(f"No slides found in latest carousel folder: {latest_folder}")
        raise FileNotFoundError(f"No slides found in latest carousel folder: {latest_folder}")

    sorted_slides = sorted(image_files)
    logger.info(f"Found {len(sorted_slides)} slides. Processing into video sequence...")

    clips = []
    for slide_path in sorted_slides:
        # Updated to MoviePy 2.x syntax: with_duration() and resized()
        clip = ImageClip(slide_path).with_duration(slide_duration)
        
        if clip.w / clip.h <= 9 / 16:
            clip_resized = clip.resized(height=1920)
        else:
            clip_resized = clip.resized(width=1080)

        # Centered canvas composition using CompositeVideoClip
        background = ColorClip(size=(1080, 1920), color=(18, 18, 18)).with_duration(slide_duration)
        final_slide = CompositeVideoClip([background, clip_resized.with_position("center")])
        clips.append(final_slide)

    final_carousel_clip = concatenate_videoclips(clips, method="compose")

    REELS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_mp4_path = REELS_OUTPUT_DIR / f"{latest_folder.name}_carousel_reel.mp4"

    logger.info(f"Rendering carousel Reel ({len(sorted_slides)} slides, {len(sorted_slides) * slide_duration}s total)...")

    final_carousel_clip.write_videofile(
        str(output_mp4_path),
        fps=fps,
        codec="libx264",
        audio=False,
        preset="medium",
        logger=None
    )

    final_carousel_clip.close()
    for c in clips:
        c.close()

    logger.info(f"Carousel MP4 successfully rendered: {output_mp4_path}")
    return str(output_mp4_path)


def convert_latest_image_to_mp4(
    image_dir: Path = SINGLE_IMAGE_DIR, 
    duration: int = 7, 
    fps: int = 30
) -> str:
    latest_image_path = get_latest_image(image_dir)
    image_path_obj = Path(latest_image_path)
    
    REELS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_mp4_path = REELS_OUTPUT_DIR / f"{image_path_obj.stem}_reel.mp4"

    logger.info(f"Converting latest image '{image_path_obj.name}' to MP4 (9:16, {duration}s)...")

    # Updated to MoviePy 2.x syntax
    clip = ImageClip(str(latest_image_path)).with_duration(duration)

    if clip.w / clip.h <= 9 / 16:
        clip_resized = clip.resized(height=1920)
    else:
        clip_resized = clip.resized(width=1080)

    background = ColorClip(size=(1080, 1920), color=(18, 18, 18)).with_duration(duration)
    final_clip = CompositeVideoClip([background, clip_resized.with_position("center")])

    final_clip.write_videofile(
        str(output_mp4_path),
        fps=fps,
        codec="libx264",
        audio=False,
        preset="medium",
        logger=None
    )

    final_clip.close()
    clip.close()

    logger.info(f"MP4 successfully rendered: {output_mp4_path}")
    return str(output_mp4_path)


def upload_local_media_temp(file_path: str) -> str:
    """Uploads a local media file (image or video) to Cloudinary to generate a public HTTPS URL required by Buffer."""
    import cloudinary
    import cloudinary.uploader

    logger.info(f"Uploading media file to Cloudinary: {file_path}")

    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True,
    )

    is_video = str(file_path).lower().endswith((".mp4", ".mov", ".avi", ".mkv"))
    resource_type = "video" if is_video else "image"

    try:
        response = cloudinary.uploader.upload(
            file_path, 
            folder="temp_buffer_uploads",
            resource_type=resource_type
        )
        public_url = response.get("secure_url")

        if not public_url:
            logger.error(f"Cloudinary upload failed. Response: {response}")
            raise Exception(f"Failed to upload media to Cloudinary: {response}")

        logger.info(f"Cloudinary Upload Success ({resource_type}): {public_url}")
        return public_url
    except Exception as e:
        logger.exception(f"Exception raised during Cloudinary upload for {file_path}")
        raise e


def wait_for_cloudinary_urls(urls: list[str], timeout: int = 15, poll_interval: float = 0.5) -> bool:
    """Polls Cloudinary URLs via HTTP HEAD requests until they return 200 OK and are cached on CDN."""
    start_time = time.time()
    pending_urls = list(urls)

    logger.info("Verifying Cloudinary CDN propagation for uploaded assets...")

    while pending_urls and (time.time() - start_time) < timeout:
        for url in list(pending_urls):
            try:
                response = requests.head(url, timeout=3)
                if response.status_code == 200:
                    pending_urls.remove(url)
            except requests.RequestException:
                pass

        if pending_urls:
            time.sleep(poll_interval)

    if pending_urls:
        logger.warning(f"Timeout reached. {len(pending_urls)} URLs still pending CDN readiness.")
        return False

    logger.info("All Cloudinary image URLs are verified accessible on CDN.")
    return True


def post_image_to_buffer(image_urls: list[str], caption: str, music_recommendation: str = None) -> dict:
    """Sends hosted image URLs and metadata payload to Buffer GraphQL API."""
    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post {
            id
            status
          }
        }
        ... on MutationError {
          message
        }
      }
    }
    """

    final_caption = caption
    if music_recommendation:
        final_caption = f"{caption}\n\n🎵 Suggested Track: {music_recommendation}"

    final_caption = sanitize_caption_for_instagram(final_caption)
    assets = [{"image": {"url": url}} for url in image_urls]

    variables = {
        "input": {
            "channelId": BUFFER_CHANNEL_ID,
            "text": final_caption,
            "schedulingType": "automatic",
            "mode": "addToQueue",
            "assets": assets,
            "metadata": {
                "instagram": {
                    "type": "post"
                }
            }
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BUFFER_API_KEY}"
    }

    logger.info(f"Sending GraphQL payload to Buffer for Channel ID: {BUFFER_CHANNEL_ID}")

    response = requests.post(
        "https://api.buffer.com",
        headers=headers,
        json={"query": mutation, "variables": variables}
    )

    logger.info(f"Buffer API HTTP Status Code: {response.status_code}")

    try:
        res_json = response.json()
        logger.info(f"Buffer Raw API Response: {res_json}")

        if "errors" in res_json:
            logger.error(f"Buffer GraphQL Errors: {res_json['errors']}")

        create_post_data = res_json.get("data", {}).get("createPost", {})
        if "message" in create_post_data:
            logger.error(f"Buffer Mutation Error Message: {create_post_data['message']}")

        return res_json
    except Exception as e:
        logger.error(f"Failed to parse Buffer HTTP response text: {response.text}")
        raise e


def post_reel_to_buffer(video_url: str, caption: str, music_recommendation: str = None) -> dict:
    """Sends hosted video URL and metadata payload to Buffer GraphQL API as an Instagram Reel."""
    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post {
            id
            status
          }
        }
        ... on MutationError {
          message
        }
      }
    }
    """

    final_caption = caption
    if music_recommendation:
        final_caption = f"{caption}\n\n🎵 Suggested Track: {music_recommendation}"

    final_caption = sanitize_caption_for_instagram(final_caption)

    variables = {
        "input": {
            "channelId": BUFFER_CHANNEL_ID,
            "text": final_caption,
            "schedulingType": "automatic",
            "mode": "addToQueue",
            "assets": [{"video": {"url": video_url}}],
            "metadata": {
                "instagram": {
                    "type": "reel",
                    "shouldShareToFeed": True
                }
            }
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BUFFER_API_KEY}"
    }

    logger.info(f"Sending Reel GraphQL payload to Buffer for Channel ID: {BUFFER_CHANNEL_ID}")

    response = requests.post(
        "https://api.buffer.com",
        headers=headers,
        json={"query": mutation, "variables": variables}
    )

    try:
        res_json = response.json()
        logger.info(f"Buffer Raw API Response: {res_json}")
        return res_json
    except Exception as e:
        logger.error(f"Failed to parse Buffer HTTP response text: {response.text}")
        raise e


def publish_latest_single_image(caption: str, music_recommendation: str = None):
    """Main workflow function to fetch local image, upload, and publish single post via Buffer."""
    logger.info("Starting publish workflow for single image...")
    local_image_path = get_latest_image(SINGLE_IMAGE_DIR)
    public_image_url = upload_local_media_temp(local_image_path)
    
    wait_for_cloudinary_urls([public_image_url])
    
    response = post_image_to_buffer([public_image_url], caption, music_recommendation=music_recommendation)
    return response


def publish_carousel_post(media_paths: list[str] = None, caption: str = "", music_recommendation: str = None):
    """Workflow function to upload multiple image paths and publish a Carousel post via Buffer."""
    if not media_paths:
        base_dir = Path(CAROUSEL_DIR)
        subdirs = [p for p in base_dir.iterdir() if p.is_dir()]
        if not subdirs:
            raise FileNotFoundError(f"No carousel folders found in {base_dir}")

        latest_folder = max(subdirs, key=os.path.getmtime)
        extensions = ("*.jpg", "*.jpeg", "*.png")
        image_files = []
        for ext in extensions:
            image_files.extend(glob.glob(str(latest_folder / ext)))

        media_paths = sorted(image_files)

    logger.info(f"Starting publish workflow for carousel post ({len(media_paths)} images)...")
    public_urls = [upload_local_media_temp(img_path) for img_path in media_paths]

    wait_for_cloudinary_urls(public_urls)

    response = post_image_to_buffer(public_urls, caption, music_recommendation=music_recommendation)
    return response


def publish_carousel_as_reel(caption: str = "", music_recommendation: str = None, slide_duration: float = 3.0):
    """Workflow function to convert latest carousel slides into an MP4 video and publish as an Instagram Reel."""
    logger.info("Starting publish workflow for Carousel Reel...")
    local_mp4_path = convert_latest_carousel_to_mp4(slide_duration=slide_duration)
    public_video_url = upload_local_media_temp(local_mp4_path)

    wait_for_cloudinary_urls([public_video_url])
    return post_reel_to_buffer(public_video_url, caption, music_recommendation=music_recommendation)


if __name__ == "__main__":
    caption_text = "Daily Whisper ✨ - Automated Carousel Post #dailywhisper #quotes #mindfulness #positivity #peace"
    music_track = "Keep Your Head Up - Ben Howard"
    
    result = publish_carousel_post(caption=caption_text, music_recommendation=music_track)
    print("Buffer Response:", result)