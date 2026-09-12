from datetime import datetime
import io
import json
from pathlib import Path
import random
from google import genai
from google.genai import types
from PIL import Image

# Target resolution configuration
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1350

def get_random_theme() -> str:
    """Selects a random theme across diverse emotional and inspirational categories."""
    themes = [
        "self-strength and resilience",
        "inner peace and mindfulness",
        "personal growth and overcoming obstacles",
        "courage and finding your purpose",
        "emotional healing and hope",
        "deep love and romantic connection",
        "gratitude and appreciating small moments",
        "self-discovery and authenticity",
    ]
    return random.choice(themes)


def get_random_style() -> str:
    """Returns a random visual style prompt selected across expanded aesthetic categories."""
    categories = [
        "realistic_photography",
        "digital_art_anime",
        "vintage_retro",
        "minimalist_fine_art",
        "illustration_painting",
    ]
    chosen_category = random.choice(categories)

    if chosen_category == "realistic_photography":
        styles = [
            "cinematic 35mm photography with soft natural lighting and golden hour tones",
            "candid high-resolution portrait photo with soft bokeh and shallow depth of field",
            "moody editorial lifestyle photography with dramatic contrast and rich atmospheric depth",
            "documentary-style street photography shot on analog film with subtle grain",
            "dreamy golden-hour architectural photo with warm, ambient reflections",
        ]
        return f"A realistic photo style: {random.choice(styles)}"

    elif chosen_category == "digital_art_anime":
        styles = [
            "vibrant anime style illustration with clean line art, dramatic backlighting, and soft lens flare",
            "modern 3D digital art render with sleek ambient glow, soft shading, and cinematic atmosphere",
            "cozy Studio Ghibli-inspired digital scene with lush natural elements and soft pastel lighting",
            "futuristic cyberpunk aesthetic with neon luminescence and atmospheric mist",
            "stylized fantasy digital concept art with dynamic lighting and rich color palettes",
        ]
        return f"A digital art style: {random.choice(styles)}"

    elif chosen_category == "vintage_retro":
        styles = [
            "retro 1970s film photo with warm faded film stock, gentle light leaks, and analog texture",
            "80s synthwave graphic novel art style with neon accents and high contrast",
            "nostalgic 90s polaroid photo aesthetic with soft muted colors and film grain",
            "vintage vintage poster art with bold retro typography elements and screen-print texture",
        ]
        return f"A vintage aesthetic style: {random.choice(styles)}"

    elif chosen_category == "minimalist_fine_art":
        styles = [
            "minimalist fine-art photo with clean negative space, soft shadows, and subtle color palette",
            "abstract surrealist digital art with soft atmospheric gradients and geometric balance",
            "scandandi-inspired clean aesthetic with neutral earthy tones and gentle directional light",
            "monochromatic black-and-white fine art photography with high tonal range and deep contrast",
        ]
        return f"A minimalist fine art style: {random.choice(styles)}"

    else:  # illustration_painting
        styles = [
            "cozy watercolor painting with wet-on-wet textures, soft bleeding edges, and pastel tones",
            "textured oil painting aesthetic with visible palette knife strokes and rich color blending",
            "whimsical storybook vector illustration with expressive detail and soft hand-drawn lines",
            "impressionist brushstroke painting with vibrant light play and painterly feel",
            "modern gouache illustration style with flat bold shapes and hand-crafted textures",
        ]
        return f"An illustrative painting style: {random.choice(styles)}"


def generate_single_image_post(
    theme: str = None, force_panels: int = None
) -> tuple[str, str, str, str, str]:
    """Generates an Instagram post image, quote, explanation, hashtags, and music recommendation.

    :param theme: Optional theme. If None, a random theme is selected.
    :param force_panels: Optional integer (1, 2, or 3) to force single panel or
      split story mode.
    :return: Tuple containing (image_path, short_sentence, explanation, hashtags, music_recommendation)
    """
    client = genai.Client()

    # Determine theme if not explicitly passed
    active_theme = theme if theme else get_random_theme()

    # Determine panel count: 1 (single image) or 2/3 (split story image)
    num_panels = (
        force_panels
        if force_panels in [1, 2, 3]
        else random.choice([1, 2, 3])
    )
    chosen_style = get_random_style()

    # Subject selection based on theme context (single person or couple)
    is_relationship_theme = any(
        kw in active_theme.lower() for kw in ["love", "couple", "romantic", "connection"]
    )
    if is_relationship_theme:
        character_desc = "Exactly one couple (a man and a woman)"
        subject_instruction = "The SAME MAN and SAME WOMAN must appear in every panel. Do not introduce any third parties."
    else:
        character_desc = "A single central subject (either a man or a woman)"
        subject_instruction = "The EXACT SAME main person must appear as the sole focus in every panel."

    if num_panels == 1:
        # 1. Single panel sentence generation with explanation and hashtags
        text_prompt = (
            f"Write an Instagram post caption package for the theme '{active_theme}'.\n"
            f"1. A single short, impactful, and inspiring sentence (4-6 words max).\n"
            f"2. A 2-3 sentence inspiring explanation reflecting deeply on the sentence.\n"
            f"3. 6 to 9 relevant, high-engagement Instagram hashtags tailored specifically to '{active_theme}' (always include #thisisdailywhisper).\n"
            f"4. A suggested song title and artist available on Instagram Audio that matches the mood of the sentence.\n\n"
            f"Format strictly as:\n"
            f"QUOTE: <your quote without quotation marks>\n"
            f"EXPLANATION: <your explanation>\n"
            f"HASHTAGS: <your hashtags separated by spaces>\n"
            f"MUSIC: <song name - artist name or genre keyword search>"
        )
        sentence_response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=text_prompt,
        )
        raw_text = sentence_response.text.strip()
        
        short_sentence = ""
        explanation = ""
        hashtags = "#thisisdailywhisper #inspiration #motivation"
        music_recommendation = ""

        for line in raw_text.splitlines():
            if line.startswith("QUOTE:"):
                short_sentence = line.replace("QUOTE:", "").strip().replace('"', "")
            elif line.startswith("EXPLANATION:"):
                explanation = line.replace("EXPLANATION:", "").strip()
            elif line.startswith("HASHTAGS:"):
                hashtags = line.replace("HASHTAGS:", "").strip()
            elif line.startswith("MUSIC:"):
                music_recommendation = line.replace("MUSIC:", "").strip()

        if not short_sentence:
            short_sentence = raw_text.splitlines()[0].replace('"', "")

        image_prompt = (
            f"{chosen_style} inspired by the theme '{active_theme}'. "
            f"Featuring {character_desc} in a scene that visually captures the emotional meaning of: '{short_sentence}'. "
            f"The text '{short_sentence}' is overlayed clearly in elegant typography with high contrast."
        )

    else:
        # 2. Multi-panel split story sentence generation with explanation and hashtags
        text_prompt = (
            f"Write an Instagram multi-panel story post caption package for the theme '{active_theme}'.\n"
            f"1. A short, inspiring {num_panels}-part story quote (total 6-10 words max) separated strictly by '|'.\n"
            f"2. A 2-3 sentence inspiring explanation reflecting deeply on the story.\n"
            f"3. 6 to 9 relevant, high-engagement Instagram hashtags tailored specifically to '{active_theme}' (always include #thisisdailywhisper).\n"
            f"4. A suggested song title and artist available on Instagram Audio that matches the mood of the sentence.\n\n"
            f"Format strictly as:\n"
            f"QUOTE: <segment 1 | segment 2 | segment 3>\n"
            f"EXPLANATION: <your explanation>\n"
            f"HASHTAGS: <your hashtags separated by spaces>\n"
            f"MUSIC: <song name - artist name or genre keyword search>"
        )
        sentence_response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=text_prompt,
        )
        raw_text = sentence_response.text.strip()

        quote_raw = ""
        explanation = ""
        hashtags = "#thisisdailywhisper #inspiration #motivation"
        music_recommendation = ""

        for line in raw_text.splitlines():
            if line.startswith("QUOTE:"):
                quote_raw = line.replace("QUOTE:", "").strip().replace('"', "")
            elif line.startswith("EXPLANATION:"):
                explanation = line.replace("EXPLANATION:", "").strip()
            elif line.startswith("HASHTAGS:"):
                hashtags = line.replace("HASHTAGS:", "").strip()
            elif line.startswith("MUSIC:"):
                music_recommendation = line.replace("MUSIC:", "").strip()

        parts = [p.strip() for p in quote_raw.split("|") if p.strip()]

        if len(parts) != num_panels:
            parts = [f"Part {i+1}" for i in range(num_panels)]

        short_sentence = " ".join(parts)

        panel_descriptions = []
        for idx, part in enumerate(parts, 1):
            panel_descriptions.append(
                f"Panel {idx}: Represents '{part}', with the text '{part}' clearly overlayed at the top."
            )

        layout_type = f"{num_panels}-row vertically stacked layout"
        story_instructions = " ".join(panel_descriptions)

        image_prompt = (
            f"{chosen_style} structured as a single image with a {layout_type} themed around '{active_theme}'. "
            f"MAIN SUBJECT: {character_desc}. "
            f"STRICT REQUIREMENT: {subject_instruction} "
            f"{story_instructions} "
            f"Ensure clean horizontal panel borders and high contrast legibility for text."
        )

    # Generate Image via Gemini (4:5 Aspect Ratio)
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=image_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio="4:5",
            ),
        ),
    )

    output_dir = Path("output") / "Single_Image"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_path = output_dir / f"single_image_post_{timestamp}.png"

    image_saved = False
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                # Open generated image bytes, resize to exactly 1080x1350 px, and save
                raw_image = Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
                if raw_image.size != (TARGET_WIDTH, TARGET_HEIGHT):
                    raw_image = raw_image.resize(
                        (TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS
                    )
                raw_image.save(output_path, "PNG")
                image_saved = True
                break

    if not image_saved:
        raise RuntimeError("Gemini failed to return an image in the response.")

    return str(output_path), short_sentence, explanation, hashtags, music_recommendation