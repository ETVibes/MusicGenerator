import os
import time
import cloudinary
import cloudinary.uploader
import requests
from src.single_image_generator import generate_single_image_post

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

def upload_to_cloudinary(local_image_path: str) -> tuple[str, str]:
    """Uploads local image to Cloudinary and returns (public_url, public_id)."""
    response = cloudinary.uploader.upload(
        local_image_path,
        folder="etvibes_auto",
        overwrite=True
    )
    return response["secure_url"], response["public_id"]


def publish_container_to_instagram(public_image_url: str, caption: str) -> str:
    """Posts public image URL to Instagram Graph API."""
    account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")

    if not account_id or not access_token:
        raise ValueError("Missing INSTAGRAM_ACCOUNT_ID or INSTAGRAM_ACCESS_TOKEN.")

    # 1. Create Media Container
    container_url = f"https://graph.facebook.com/v19.0/{account_id}/media"
    container_payload = {
        "image_url": public_image_url,
        "caption": caption,
        "access_token": access_token,
    }
    res = requests.post(container_url, data=container_payload)
    res.raise_for_status()
    creation_id = res.json()["id"]

    # Wait 5 seconds for Instagram server processing
    time.sleep(5)

    # 2. Publish Media
    publish_url = f"https://graph.facebook.com/v19.0/{account_id}/media_publish"
    publish_payload = {
        "creation_id": creation_id,
        "access_token": access_token,
    }
    pub_res = requests.post(publish_url, data=publish_payload)
    pub_res.raise_for_status()

    return pub_res.json()["id"]


def run_automated_post_pipeline(theme: str = "Inspirational & Uplifting") -> dict:
    """End-to-end headless pipeline."""
    print("1/4: Generating sentence and single image via Gemini...")
    local_image_path, sentence = generate_single_image_post(theme)

    print("2/4: Uploading to Cloudinary...")
    public_url, public_id = upload_to_cloudinary(local_image_path)

    try:
        print("3/4: Publishing to Instagram Feed...")
        caption = f"{sentence}\n\n#inspiration #vibes #dailyquote #aiart"
        post_id = publish_container_to_instagram(public_url, caption)
        print(f"✅ Published successfully! Instagram Post ID: {post_id}")
        return {"status": "success", "post_id": post_id, "sentence": sentence}

    finally:
        print("4/4: Cleaning up Cloudinary temp image...")
        cloudinary.uploader.destroy(public_id)


if __name__ == "__main__":
    # Allows running directly for testing or via Cron/GitHub Actions
    run_automated_post_pipeline()