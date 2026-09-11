import base64
from pathlib import Path
import gradio as gr
from src.image_generator import generate_images_for_quote
from src.text_generator import generate_vibe_and_text
from src.single_image_generator import generate_single_image_post
from src.Publish_IG_Post import publish_latest_single_image

# Define project base path and local asset paths
BASE_DIR = Path(__file__).parent
INSPIRATIONAL_IMG_PATH = BASE_DIR / "assets" / "inspirational.png"
ROMANCE_IMG_PATH = BASE_DIR / "assets" / "romance.png"
INSTA_SINGLE_IMG_PATH = BASE_DIR / "assets" / "Instagram_Single_Image.png"
INSTA_SHORT_IMG_PATH = BASE_DIR / "assets" / "Instagram_Short.png"


def get_image_base64(image_path: Path) -> str:
    """Converts a local image file to a base64 Data URL string."""
    if not image_path.exists():
        return ""
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return f"data:image/png;base64,{encoded_string}"


inspirational_b64 = get_image_base64(INSPIRATIONAL_IMG_PATH)
romance_b64 = get_image_base64(ROMANCE_IMG_PATH)
insta_single_b64 = get_image_base64(INSTA_SINGLE_IMG_PATH)
insta_short_b64 = get_image_base64(INSTA_SHORT_IMG_PATH)

custom_css = """
/* Reset Gradio default panel backgrounds and paddings */
.gradio-container, 
.gr-form, 
.form, 
.block,
div[class*="block"] {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

#run-btn {
    background-color: #1520A6 !important;
    color: white !important;
    border: none !important;
    max-width: 180px !important;
    padding: 6px 14px !important;
    font-size: 13px !important;
    margin-top: 8px !important;
    border-radius: 6px !important;
}

#run-btn:hover {
    background-color: #0F177C !important;
}

#ig-publish-btn {
    background-color: #E1306C !important;
    color: white !important;
    border: none !important;
    max-width: 220px !important;
    padding: 6px 14px !important;
    font-size: 13px !important;
    margin-top: 8px !important;
    border-radius: 6px !important;
}

#ig-publish-btn:hover {
    background-color: #C13584 !important;
}

/* Custom Image Card Buttons for Themes */
.card-btn {
    position: relative !important;
    width: 100px !important;
    height: 100px !important;
    min-width: 100px !important;
    max-width: 100px !important;
    padding: 0 !important;
    overflow: hidden !important;
    border: none !important;
    background-size: contain !important;
    background-position: center !important;
    background-repeat: no-repeat !important;
    cursor: pointer !important;
    transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out !important;
}

.card-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
}

/* Small Square Buttons for Format Icons with full image display */
.format-card-btn {
    position: relative !important;
    width: 90px !important;
    height: 90px !important;
    min-width: 90px !important;
    max-width: 90px !important;
    border-radius: 10px !important;
    padding: 0 !important;
    overflow: hidden !important;
    border: none !important;
    background-size: contain !important;
    background-position: center !important;
    background-repeat: no-repeat !important;
    cursor: pointer !important;
    transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out !important;
}

.format-card-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
}

/* Position White Bold Labels at the Top of Each Card */
#format-single-card::after {
    content: "Single Image";
    position: absolute;
    top: 3px;
    left: 0;
    right: 0;
    text-align: center;
    color: #000000 !important;
    font-weight: 700 !important;
    font-size: 11px !important;
    pointer-events: none;
}

#format-short-card::after {
    content: "Short";
    position: absolute;
    top: 3px;
    left: 0;
    right: 0;
    text-align: center;
    color: #000000 !important;
    font-weight: 700 !important;
    font-size: 11px !important;
    pointer-events: none;
}

#inspirational-card::after {
    content: "Inspirational & Uplifting";
    position: absolute;
    top: 5px;
    left: 0;
    right: 0;
    text-align: center;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 11px !important;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8), 0 0 8px rgba(0, 0, 0, 0.6);
    pointer-events: none;
}

#romance-card::after {
    content: "Love & Romance";
    position: absolute;
    top: 5px;
    left: 0;
    right: 0;
    text-align: center;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 11px !important;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8), 0 0 8px rgba(0, 0, 0, 0.6);
    pointer-events: none;
}

/* Single Image Flow: Compact, left-aligned layout */
.single-image-gallery {
    max-width: 280px !important;
    margin-left: 0 !important;
    margin-right: auto !important;
}

.single-image-gallery img {
    max-height: 400px !important;
    object-fit: contain !important;
}

/* Short Flow: Force full width across columns */
.short-flow-gallery {
    width: 100% !important;
    max-width: 100% !important;
}

.short-flow-gallery .grid-wrap {
    display: grid !important;
    grid-template-columns: repeat(4, 1fr) !important;
    gap: 12px !important;
    width: 100% !important;
}

.short-flow-gallery img {
    width: 100% !important;
    max-height: 380px !important;
    object-fit: contain !important;
}
"""


def select_format_step(selected_format):
    """Saves format choice and unhides the theme selection block."""
    return selected_format, gr.update(visible=True)


def on_theme_click(theme_selection, output_format, progress=gr.Progress()):
    """Routes generation based on format."""
    if output_format == "Single Image":
        progress(0.4, desc="Generating sentence & image...")
        image_path, sentence = generate_single_image_post(theme_selection)

        status = f"### Theme: {theme_selection}\n**Embedded Sentence:** \"{sentence}\""

        progress(1.0, desc="Done!")
        return (
            status,
            sentence,
            [sentence],
            gr.update(visible=False),  # Hide Short approval row
            gr.update(visible=True),   # Unhide Single Image publishing row
            gr.update(value=[image_path], columns=1, elem_classes=["single-image-gallery"], visible=True),
            ""                         # Clear previous publish status
        )
    else:
        progress(0.3, desc=f"Generating {theme_selection} quote...")
        script_data = generate_vibe_and_text(selected_theme=theme_selection)

        theme = script_data.get("sub_genre", theme_selection)
        quote = script_data.get("inspiring_quote", "")
        sentences = script_data.get("sentences", [])

        formatted_quote = f"### Selected Theme: {theme_selection}\n"
        formatted_quote += f"**Format:** {output_format}\n\n"
        formatted_quote += f"**Sub-Genre:** {theme}\n\n"
        formatted_quote += f"**Full Quote:** \"{quote}\"\n\n"
        formatted_quote += "**Overlay Lines:**\n"
        for idx, line in enumerate(sentences, 1):
            formatted_quote += f"- Part {idx}: {line}\n"

        progress(1.0, desc="Quote ready for review!")

        return (
            formatted_quote,
            quote,
            sentences,
            gr.update(visible=True),   # Unhide Short approval row
            gr.update(visible=False),  # Hide Single Image publishing row
            gr.update(visible=False),
            ""                         # Clear previous publish status
        )


def step2_generate_images(quote, sentences, progress=gr.Progress()):
    """Step 2: Generates 4 scenes for Short format."""
    if not quote:
        return gr.update()

    progress(0.2, desc="Generating 4 narrative visual prompts...")
    progress(0.5, desc="Creating images via Gemini...")
    image_paths = generate_images_for_quote(quote, sentences)

    progress(1.0, desc="Done!")

    return gr.update(value=image_paths, columns=4, elem_classes=["short-flow-gallery"], visible=True)


def handle_publish_to_instagram(sentence: str, progress=gr.Progress()):
    """Publishes the latest generated single image to Instagram via Buffer."""
    if not sentence:
        return "❌ **Error:** No sentence/caption available to publish."

    progress(0.3, desc="Uploading image temporarily...")
    progress(0.7, desc="Sending post request to Buffer API...")

    caption_text = f"{sentence}\n\n✨ #dailywhisper #inspiration #motivation"
    res = publish_latest_single_image(caption_text)

    post_data = res.get("data", {}).get("createPost", {})
    if "post" in post_data:
        post_id = post_data["post"].get("id", "N/A")
        return f"🎉 **Successfully published to Instagram!** (Buffer Post ID: `{post_id}`)"
    else:
        err_msg = res.get("errors", [{}])[0].get("message", str(res))
        return f"❌ **Publishing Failed:** {err_msg}"


with gr.Blocks(title="ETVibes Content Generator") as demo:
    gr.Markdown("# 🎬 ETVibes Content Generator")
    gr.Markdown(
        "Select a format and theme picture below to generate your content."
    )

    # State variables
    selected_format = gr.State("Short")
    selected_theme = gr.State("Inspirational & Uplifting")
    state_quote = gr.State("")
    state_sentences = gr.State([])

    # Step 0: Format Selection
    gr.Markdown("### Select Format")
    with gr.Row():
        single_img_btn = gr.Button(
            value="",
            elem_classes=["format-card-btn"],
            elem_id="format-single-card",
        )
        short_btn = gr.Button(
            value="",
            elem_classes=["format-card-btn"],
            elem_id="format-short-card",
        )

    # Step 1: Theme Selection (Revealed once format is chosen)
    with gr.Column(visible=False) as theme_section:
        gr.Markdown("### Select a theme to generate a quote")
        with gr.Row():
            inspirational_btn = gr.Button(
                value="",
                elem_classes=["card-btn"],
                elem_id="inspirational-card",
            )
            romance_btn = gr.Button(
                value="",
                elem_classes=["card-btn"],
                elem_id="romance-card",
            )

    # Generated quote display
    output_text = gr.Markdown(label="Generated Lines & Vibe")

    # Action buttons directly beneath the quote for Short format
    with gr.Row(visible=False) as approval_row:
        approve_btn = gr.Button(
            "✅ Continue to Images", elem_id="run-btn", size="sm"
        )
        regenerate_btn = gr.Button(
            "🔄 Generate New quote", elem_id="run-btn", size="sm"
        )

    # Action button for Single Image Instagram publishing
    with gr.Row(visible=False) as single_image_pub_row:
        publish_ig_btn = gr.Button(
            "📸 Publish to Instagram", elem_id="ig-publish-btn", size="sm"
        )

    # Display publish feedback
    publish_status = gr.Markdown("")

    # Image gallery placed at the bottom
    output_gallery = gr.Gallery(
        label="Generated Scenes",
        columns=4,
        rows=1,
        object_fit="contain",
        visible=False,
    )

    # Inject dynamic base64 styles for all card backgrounds
    card_styles = f"""
    #format-single-card {{
        background-image: url('{insta_single_b64}') !important;
    }}
    #format-short-card {{
        background-image: url('{insta_short_b64}') !important;
    }}
    #inspirational-card {{
        background-image: url('{inspirational_b64}') !important;
    }}
    #romance-card {{
        background-image: url('{romance_b64}') !important;
    }}
    """
    gr.HTML(f"<style>{card_styles}</style>")

    # Format Button Handlers
    single_img_btn.click(
        fn=lambda: "Single Image",
        outputs=[selected_format],
    ).then(
        fn=select_format_step,
        inputs=[selected_format],
        outputs=[selected_format, theme_section],
    )

    short_btn.click(
        fn=lambda: "Short",
        outputs=[selected_format],
    ).then(
        fn=select_format_step,
        inputs=[selected_format],
        outputs=[selected_format, theme_section],
    )

    # Theme Button Handlers
    inspirational_btn.click(
        fn=lambda: "Inspirational & Uplifting",
        outputs=[selected_theme],
    ).then(
        fn=on_theme_click,
        inputs=[selected_theme, selected_format],
        outputs=[
            output_text,
            state_quote,
            state_sentences,
            approval_row,
            single_image_pub_row,
            output_gallery,
            publish_status,
        ],
    )

    romance_btn.click(
        fn=lambda: "Love & Romance",
        outputs=[selected_theme],
    ).then(
        fn=on_theme_click,
        inputs=[selected_theme, selected_format],
        outputs=[
            output_text,
            state_quote,
            state_sentences,
            approval_row,
            single_image_pub_row,
            output_gallery,
            publish_status,
        ],
    )

    # Regenerate Button Listener
    regenerate_btn.click(
        fn=on_theme_click,
        inputs=[selected_theme, selected_format],
        outputs=[
            output_text,
            state_quote,
            state_sentences,
            approval_row,
            single_image_pub_row,
            output_gallery,
            publish_status,
        ],
    )

    # Step 2 Button Listener (Short Flow)
    approve_btn.click(
        fn=step2_generate_images,
        inputs=[state_quote, state_sentences],
        outputs=[output_gallery],
    )

    # Single Image Instagram Publish Handler
    publish_ig_btn.click(
        fn=handle_publish_to_instagram,
        inputs=[state_quote],
        outputs=[publish_status],
    )

if __name__ == "__main__":
    demo.launch(inbrowser=True, css=custom_css)