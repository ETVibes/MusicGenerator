import os
import glob
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BUFFER_API_KEY = os.getenv("BUFFER_API_KEY")
BUFFER_CHANNEL_ID = os.getenv("BUFFER_INSTAGRAM_CHANNEL_ID")
# Dynamically set IMAGE_DIR relative to the repository root directory
BASE_DIR = Path(__file__).resolve().parent.parent
IMAGE_DIR = BASE_DIR / "output" / "Single_Image"


def get_latest_image(folder_path: str) -> str:
    """Finds the most recently modified image (.jpg, .jpeg, .png) in the specified directory."""
    extensions = ("*.jpg", "*.jpeg", "*.png")
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(folder_path, ext)))

    if not files:
        raise FileNotFoundError(f"No image files found in {folder_path}")

    return max(files, key=os.path.getmtime)


def upload_local_image_temp(file_path: str) -> str:
    """Uploads a local image file to Catbox.moe to generate a public HTTPS URL required by Buffer."""
    upload_url = "https://catbox.moe/user/api.php"
    
    with open(file_path, "rb") as file_data:
        response = requests.post(
            upload_url,
            data={"reqtype": "fileupload"},
            files={"fileToUpload": file_data},
            timeout=15
        )

    if response.status_code != 200 or not response.text.startswith("https://"):
        raise Exception(f"Failed to upload image temporarily: {response.text}")

    return response.text.strip()


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