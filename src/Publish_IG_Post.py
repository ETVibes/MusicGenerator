import os
import glob
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BUFFER_API_KEY = os.getenv("BUFFER_API_KEY")
BUFFER_CHANNEL_ID = os.getenv("BUFFER_INSTAGRAM_CHANNEL_ID")

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# Dynamically set IMAGE_DIR relative to project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
IMAGE_DIR = BASE_DIR / "output" / "Single_Image"


def get_latest_image(folder_path: Path) -> str:
    """Finds the most recently modified image (.jpg, .jpeg, .png) in the specified directory."""
    folder_path = Path(folder_path)
    extensions = ("*.jpg", "*.jpeg", "*.png")
    files = []
    for ext in extensions:
        files.extend(glob.glob(str(folder_path / ext)))

    if not files:
        raise FileNotFoundError(f"No image files found in {folder_path}")

    return max(files, key=os.path.getmtime)


def upload_local_image_temp(file_path: str) -> str:
    """Uploads a local image file to Cloudinary to generate a public HTTPS URL required by Buffer."""
    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True,
    )

    response = cloudinary.uploader.upload(file_path, folder="temp_buffer_uploads")
    public_url = response.get("secure_url")

    if not public_url:
        raise Exception(f"Failed to upload image to Cloudinary: {response}")

    return public_url


def post_image_to_buffer(image_url: str, caption: str) -> dict:
    """Sends the hosted image URL and metadata payload to Buffer GraphQL API."""
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

    variables = {
        "input": {
            "channelId": BUFFER_CHANNEL_ID,
            "text": caption,
            "schedulingType": "automatic",
            "mode": "shareNow",
            "assets": [
                {
                    "image": {
                        "url": image_url
                    }
                }
            ],
            "metadata": {
                "instagram": {
                    "type": "post",
                    "shouldShareToFeed": True
                }
            }
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BUFFER_API_KEY}"
    }

    response = requests.post(
        "https://api.buffer.com",
        headers=headers,
        json={"query": mutation, "variables": variables}
    )

    return response.json()


def publish_latest_single_image(caption: str):
    """Main workflow function to fetch local image, upload, and publish via Buffer."""
    local_image_path = get_latest_image(IMAGE_DIR)
    public_image_url = upload_local_image_temp(local_image_path)
    response = post_image_to_buffer(public_image_url, caption)
    return response


if __name__ == "__main__":
    caption_text = "Daily Whisper ✨ - Automated Post"
    result = publish_latest_single_image(caption_text)
    print("Buffer Response:", result)
