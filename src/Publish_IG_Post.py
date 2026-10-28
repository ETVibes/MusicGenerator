"""===============================================================================
Module: Publish_IG_Post.py
Description: Automated publishing bridge for Instagram posts. Handles discovering
             locally generated images (single or carousel), uploading assets to
             Cloudinary for temporary hosting, verifying CDN availability, and
             dispatched payloads to Buffer's GraphQL API.
==============================================================================="""
import glob
import logging
import os
import random
import json
from pathlib import Path
from .config import SINGLE_IMAGE_DIR, CAROUSEL_CURRENT_DIR, REEL_DIR
import time
import requests
from dotenv import load_dotenv

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

INSTAGRAM_USER_ID = os.getenv("INSTAGRAM_USER_ID")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
"""===============================================================================
Loads background music options from assets/background_music/audio_list.json,
selects a random track based on the active theme, and queries the Instagram
Graph API to resolve its live audio_id.

Args:
    active_theme (str): The name of the active theme to select a song from.

Returns:
    dict: A dictionary containing 'title', 'singer', and the resolved 'audio_id'.
==============================================================================="""
def resolve_and_fetch_audio(active_theme: str) -> dict:
    """Loads songs from assets/background_music/audio_list.json, selects a random track, and fetches its audio_id with fallback query cleaning."""
    json_path = os.path.join("assets", "background_music", "audio_list.json")
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    themes = data.get("themes", {})
    
    normalized_theme = active_theme.strip().lower().replace(" and ", "_").replace(" ", "_")
    if normalized_theme not in themes:
        normalized_theme = "growth_courage"
        
    song_pool = themes[normalized_theme]
    selected_song = random.choice(song_pool)
    
    title = selected_song["title"]
    singer = selected_song["singer"]
    
    print(f"[AUDIO] Selected '{title}' by {singer} for theme '{active_theme}'. Querying Instagram API...")
    
    url = "https://graph.facebook.com/v26.0/ig_audio"
    
    # Create a list of fallback search queries to try in order of specificity
    import re
    clean_title = re.sub(r"\(.*?\)", "", title).strip() # Removes text in parentheses like "(Remix)"
    
    search_queries = [
        f"{title} {singer}",          # Attempt 1: Exact JSON match
        f"{clean_title} {singer}",    # Attempt 2: Cleaned title + singer
        title,                        # Attempt 3: Title only
        singer                        # Attempt 4: Singer only (last resort)
    ]
    
    audio_id = None
    for query in search_queries:
        params = {
            "audio_type": "music",
            "search_query": query,
            "user_id": INSTAGRAM_USER_ID,
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
        try:
            print(f"[AUDIO] Trying API query: '{query}'")
            response = requests.get(url, params=params)
            res_data = response.json()
            audio_list = res_data.get("audio", [])
            
            if audio_list:
                audio_id = audio_list[0].get("audio_id")
                print(f"[AUDIO] Successfully resolved audio_id using query '{query}': {audio_id}")
                break
        except Exception as e:
            print(f"[AUDIO ERROR] Query failed for '{query}': {e}")
            
    if not audio_id:
        print(f"[AUDIO WARNING] Could not resolve audio ID via API for '{title} - {singer}', even after fallbacks. Post will continue without pre-attached audio.")
        
    return {
        "title": title,
        "singer": singer,
        "audio_id": audio_id
    }
    
"""===============================================================================
    Finds the most recently modified image (.jpg, .jpeg, .png) in the specified directory.

    Args:
        folder_path (Path): Path directory to search for images.

    Returns:
        str: Absolute file path string of the most recent image.

    Raises:
        FileNotFoundError: If no image files matching supported extensions exist in folder_path.
==============================================================================="""
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

"""===============================================================================
    Finds the most recently created carousel folder and returns all sorted slide image paths within it.

    Args:
        base_carousel_dir (Path, optional): Base directory containing timestamped carousel folders.
                                            Defaults to CAROUSEL_DIR.

    Returns:
        list[str]: Sorted file path strings for each slide in the carousel.

    Raises:
        FileNotFoundError: If the base directory does not exist, contains no subdirectories,
                          or contains no valid slide images.
==============================================================================="""
def get_latest_carousel_images(base_carousel_dir: Path = CAROUSEL_CURRENT_DIR) -> list[str]:
    """Finds slide images directly from the static current carousel folder."""
    base_carousel_dir = Path(base_carousel_dir)
    if not base_carousel_dir.exists():
        logger.error(f"Carousel directory does not exist: {base_carousel_dir}")
        raise FileNotFoundError(f"Carousel directory does not exist: {base_carousel_dir}")

    extensions = ("*.jpg", "*.jpeg", "*.png")
    files = []
    for ext in extensions:
        files.extend(glob.glob(str(base_carousel_dir / ext)))

    if not files:
        logger.error(f"No slides found in carousel directory: {base_carousel_dir}")
        raise FileNotFoundError(f"No slides found in carousel directory: {base_carousel_dir}")

    sorted_slides = sorted(files)
    logger.info(f"Found {len(sorted_slides)} slide images to publish: {sorted_slides}")
    return sorted_slides

"""===============================================================================
    Finds the most recently modified video (.mp4, .mov) in the specified directory.

    Args:
        folder_path (Path): Path directory to search for videos.

    Returns:
        str: Absolute file path string of the most recent video.

    Raises:
        FileNotFoundError: If no video files matching supported extensions exist.
==============================================================================="""
def get_latest_reel_video(folder_path: Path = REEL_DIR) -> str:
    """Finds the most recently modified video (.mp4, .mov) in the specified directory."""
    folder_path = Path(folder_path)
    if not folder_path.exists():
        logger.error(f"Reel directory does not exist: {folder_path}")
        raise FileNotFoundError(f"Reel directory does not exist: {folder_path}")

    extensions = ("*.mp4", "*.mov")
    files = []
    for ext in extensions:
        files.extend(glob.glob(str(folder_path / ext)))

    if not files:
        logger.error(f"No video files found in {folder_path}")
        raise FileNotFoundError(f"No video files found in {folder_path}")

    latest_file = max(files, key=os.path.getmtime)
    logger.info(f"Selected latest reel video: {latest_file}")
    return latest_file
    
"""===============================================================================
    Uploads a local media file (image or video) to Cloudinary to generate a public HTTPS URL required by Buffer.

    Args:
        file_path (str): Local path to media file.
        resource_type (str): Type of resource ('image' or 'video'). Defaults to 'image'.

    Returns:
        str: Public HTTPS URL string generated by Cloudinary.

    Raises:
        Exception: If Cloudinary credentials fail, connection drops, or URL is omitted from response.
==============================================================================="""
def upload_local_media_temp(file_path: str, resource_type: str = "image") -> str:
    """Uploads a local media file (image or video) to Cloudinary to generate a public HTTPS URL required by Buffer."""
    import cloudinary
    import cloudinary.uploader

    logger.info(f"Uploading {resource_type} to Cloudinary: {file_path}")

    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True,
    )

    try:
        response = cloudinary.uploader.upload(file_path, resource_type=resource_type, folder="temp_buffer_uploads")
        public_url = response.get("secure_url")

        if not public_url:
            logger.error(f"Cloudinary upload failed. Response: {response}")
            raise Exception(f"Failed to upload media to Cloudinary: {response}")

        logger.info(f"Cloudinary Upload Success: {public_url}")
        return public_url
    except Exception as e:
        logger.exception(f"Exception raised during Cloudinary upload for {file_path}")
        raise e

"""===============================================================================
    Polls Cloudinary URLs via HTTP HEAD requests until they return 200 OK and are cached on CDN.

    Args:
        urls (list[str]): List of HTTPS image URLs to check.
        timeout (int, optional): Maximum seconds to wait before timing out. Defaults to 15.
        poll_interval (float, optional): Interval in seconds between checks. Defaults to 0.5.

    Returns:
        bool: True if all URLs responded with 200 OK within timeout, False otherwise.
==============================================================================="""
def wait_for_cloudinary_urls(urls: list[str], timeout: int = 15, poll_interval: float = 0.5) -> bool:
    """Polls Cloudinary URLs via HTTP HEAD requests until they return 200 OK and are fully cached on CDN."""
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

    logger.info("All Cloudinary media URLs are verified accessible on CDN.")
    return True

"""===============================================================================
    Sends hosted media asset URLs and metadata payload to Buffer GraphQL API.

    Args:
        image_urls (list[str]): Public HTTPS image URLs to attach to post.
        caption (str): Main post text caption.
        music_recommendation (str, optional): Suggested track to append to caption text.

    Returns:
        dict: Parsed JSON response dictionary returned by Buffer GraphQL endpoint.

    Raises:
        Exception: If network connection fails or HTTP response payload cannot be parsed.
==============================================================================="""
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

    # Standard AssetInput array with multiple image URLs
    assets = [{"image": {"url": url}} for url in image_urls]

    # Instagram API requires "type": "post" (Buffer converts multiple assets into a carousel automatically)
    instagram_metadata = {
        "type": "post",
        "shouldShareToFeed": True
    }

    variables = {
        "input": {
            "channelId": BUFFER_CHANNEL_ID,
            "text": final_caption,
            "schedulingType": "automatic",
            "mode": "addToQueue",  # Queues post for immediate background container assembly & publication
            "assets": assets,
            "metadata": {
                "instagram": instagram_metadata
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

"""===============================================================================
    Sends hosted video asset URL and reel metadata payload to Buffer GraphQL API.

    Args:
        video_url (str): Public HTTPS video URL to attach to post.
        caption (str): Main post text caption.
        theme (str) : The theme for the reel
        music_recommendation (str, optional): Suggested track to append to caption text.

    Returns:
        dict: Parsed JSON response dictionary returned by Buffer GraphQL endpoint.
==============================================================================="""
def post_reel_to_buffer(video_url: str, caption: str, theme: str, music_recommendation: str = None, audio_id: str = None) -> dict:
    """Sends hosted video asset URL and reel metadata payload to Buffer GraphQL API."""
    mutation = "mutation CreatePost($input: CreatePostInput!) { createPost(input: $input) { ... on PostActionSuccess { post { id status } } ... on MutationError { message } } }"

    final_caption = caption
    if music_recommendation:
        final_caption = f"{caption}\n\n🎵 Suggested Track: {music_recommendation}"

    assets = [{"video": {"url": video_url}}]

    instagram_metadata = {
        "type": "reel",
        "shouldShareToFeed": True
    }

    """ Get the audio id from the random list of songs according to the theme"""
    audio_info = resolve_and_fetch_audio(theme)
    audio_id = audio_info.get("audio_id")
    song_title = audio_info.get("title")
    singer = audio_info.get("singer")

    if audio_id:
        instagram_metadata["audio_id"] = audio_id
        logger.info(f"[AUDIO MAPPING] Selected '{song_title}' by {singer} with Instagram audio_id: {audio_id}")  
    else:
        logger.info(f"[AUDIO MAPPING] Skipping audio_id assignment for '{song_title} - {singer}'; publishing reel without pre-attached audio.")
    
    variables = {
        "input": {
            "channelId": BUFFER_CHANNEL_ID,
            "text": final_caption,
            "schedulingType": "automatic",
            "mode": "addToQueue",
            "assets": assets,
            "metadata": {
                "instagram": instagram_metadata
            }
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BUFFER_API_KEY}"
    }

    logger.info(f"Sending Reel GraphQL payload to Buffer for Channel ID: {BUFFER_CHANNEL_ID}")

    try:
        response = requests.post(
            "https://api.buffer.com",
            headers=headers,
            json={"query": mutation, "variables": variables}
        )
        
        logger.info(f"Buffer API HTTP Status Code: {response.status_code}")
        logger.info(f"Buffer Raw Response Text: {response.text}")

        # If Buffer returns a non-200 or an error page, raise it explicitly with text
        if response.status_code != 200:
            raise RuntimeError(f"Buffer API responded with status {response.status_code}: {response.text}")

        res_json = response.json()
        logger.info(f"Buffer Raw API Response: {res_json}")
        return res_json
        
    except Exception as e:
        logger.error(f"❌ [PUBLISH EXCEPTION] Failed during Buffer request: {e}")
        raise e
        
"""===============================================================================
    Main workflow function to fetch local image, upload, and publish single post via Buffer.

    Args:
        caption (str): Caption text for single image post.
        music_recommendation (str, optional): Suggested track recommendation.

    Returns:
        dict: Buffer API response payload.
==============================================================================="""
def publish_latest_single_image(caption: str, music_recommendation: str = None):
    """Main workflow function to fetch local image, upload, and publish single post via Buffer."""
    logger.info("Starting publish workflow for single image...")
    local_image_path = get_latest_image(SINGLE_IMAGE_DIR)
    public_image_url = upload_local_media_temp(local_image_path, resource_type="image")
    
    # Check CDN availability
    wait_for_cloudinary_urls([public_image_url])
    
    response = post_image_to_buffer([public_image_url], caption, music_recommendation=music_recommendation)
    return response

"""===============================================================================
    Workflow function to upload multiple image paths and publish a Carousel post via Buffer.

    Args:
        image_paths (list[str], optional): List of slide paths. Defaults to latest carousel folder if None.
        caption (str, optional): Caption text for carousel post.
        music_recommendation (str, optional): Suggested track recommendation.

    Returns:
        dict: Buffer API response payload.
==============================================================================="""
def publish_carousel_post(image_paths: list[str] = None, caption: str = "", music_recommendation: str = None):
    """Workflow function to upload multiple image paths and publish a Carousel post via Buffer."""
    if not image_paths:
        image_paths = get_latest_carousel_images()

    logger.info(f"Starting publish workflow for carousel post ({len(image_paths)} images)...")
    public_urls = [upload_local_media_temp(img_path, resource_type="image") for img_path in image_paths]

    # Actively verify CDN readiness before making the GraphQL call
    wait_for_cloudinary_urls(public_urls)

    response = post_image_to_buffer(public_urls, caption, music_recommendation=music_recommendation)
    return response

"""===============================================================================
    Workflow function to fetch local reel video, upload, and publish an Instagram Reel via Buffer.

    Args:
        caption (str): Caption text for the reel.
        theme (str) : The theme for the reel
        music_recommendation (str, optional): Suggested track recommendation.

    Returns:
        dict: Buffer API response payload.
==============================================================================="""
def publish_latest_reel(caption: str, theme: str, music_recommendation: str = None):
    """Workflow function to fetch local reel video, upload, and publish an Instagram Reel via Buffer."""
    logger.info("Starting publish workflow for Instagram Reel...")
    local_video_path = get_latest_reel_video(REEL_DIR)
    public_video_url = upload_local_media_temp(local_video_path, resource_type="video")

    wait_for_cloudinary_urls([public_video_url])

    response = post_reel_to_buffer(public_video_url, caption, theme, music_recommendation=music_recommendation)
    return response
    
if __name__ == "__main__":
    caption_text = "Daily Whisper ✨ - Automated Carousel Post"
    music_track = "Keep Your Head Up - Ben Howard"
    
    # Test publishing the latest generated carousel folder
    result = publish_carousel_post(caption=caption_text, music_recommendation=music_track)
    print("Buffer Response:", result)