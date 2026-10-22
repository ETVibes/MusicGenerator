"""===============================================================================
Module: multi_slide_carousel_generator.py
Description: Generates Instagram carousel text and a coordinated set of images.
==============================================================================="""

from datetime import datetime
import io
import json
import re
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image, ImageOps

from .prompt_config import (
    ASPECT_RATIO,
    BANNED_PHRASES,
    TARGET_HEIGHT,
    TARGET_WIDTH,
    TYPOGRAPHY_CONSTRAINT,
    build_carousel_style_block,
    draw_quote_on_image,
    get_emotional_visual_modifier,
    get_random_style,
    get_random_theme,
    get_slide_role,
    get_subject_and_instructions,
)

TEXT_MODEL = "gemini-3.6-flash"
IMAGE_MODEL = "gemini-2.5-flash-image"

def _extract_json_object(text: str) -> dict:
    """Parse a JSON object, tolerating Markdown code fences around the response."""
    cleaned = (text or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("The model response did not contain a JSON object.")
    return json.loads(cleaned[start : end + 1])

def _fallback_visual_plan(slide_quotes: list[str], theme: str) -> list[dict]:
    """Create a safe plan if visual-plan generation or JSON parsing fails."""
    plan = []
    total = len(slide_quotes)
    for index, quote in enumerate(slide_quotes, start=1):
        role, _ = get_slide_role(index, total)
        plan.append(
            {
                "slide": index,
                "role": role,
                "emotion": "emotion appropriate to the quote",
                "visual_metaphor": (
                    f"A scene that communicates the meaning of '{quote}' in the context "
                    f"of '{theme}', without using a literal text-based illustration"
                ),
                "composition": (
                    "Use a distinct camera distance, framing, and subject placement "
                    "from the other slides while preserving the shared visual style."
                ),
                "transition": "Continue the carousel's emotional progression naturally.",
            }
        )
    return plan

def _generate_visual_plan(
    client, theme: str, slide_quotes: list[str]
) -> tuple[list[dict], str]:
    """Plan the full sequence before image generation so slides tell one visual story."""
    quote_lines = "\n".join(
        f"{index}. {quote}" for index, quote in enumerate(slide_quotes, start=1)
    )
    plan_prompt = f"""
You are the visual art director for an Instagram account called thisisdailywhisper.
Create a coordinated visual storyboard for a {len(slide_quotes)}-slide carousel.

Theme: {theme}

Exact slide text, in order:
{quote_lines}

Return ONLY a valid JSON object with this structure:
{{
  "sequence_arc": "one concise sentence describing the emotional progression",
  "slides": [
    {{
      "slide": 1,
      "role": "opening | development | realization | resolution",
      "emotion": "the main emotion this slide should communicate",
      "visual_metaphor": "a concrete, imageable scene that expresses this exact slide",
      "composition": "camera distance, framing, subject placement, and environment",
      "transition": "how this visual develops from the previous slide"
    }}
  ]
}}

Requirements:
- Include exactly {len(slide_quotes)} slide objects, in the same order as the supplied text.
- Keep each visual tied to its slide's meaning; do not invent a different message.
- Plan the complete sequence together. Make the images feel like consecutive moments
  in one emotional story, not four unrelated illustrations.
- Vary the composition and visual metaphor meaningfully between slides. Do not repeat
  the same pose, camera angle, setting, or framing unless the story requires it.
- The first slide should be immediately intriguing; the final slide should feel like
  a fitting emotional conclusion. Middle slides should advance the idea.
- Keep visual ideas practical to render as a single image.
- Do not include the quote text in visual_metaphor; the image prompt will add typography.
- Do not prescribe a different art style or color palette per slide.
- Avoid relying on clichéd symbols unless they genuinely fit the quote.
"""
    try:
        response = client.models.generate_content(
            model=TEXT_MODEL,
            contents=plan_prompt,
        )
        parsed = _extract_json_object(response.text)
        raw_slides = parsed.get("slides", [])
        by_number = {
            item.get("slide"): item
            for item in raw_slides
            if isinstance(item, dict) and isinstance(item.get("slide"), int)
        }
        plan = []
        fallback = _fallback_visual_plan(slide_quotes, theme)
        for index, fallback_item in enumerate(fallback, start=1):
            candidate = by_number.get(index, {})
            plan.append(
                {
                    **fallback_item,
                    **{
                        key: str(candidate[key]).strip()
                        for key in (
                            "role",
                            "emotion",
                            "visual_metaphor",
                            "composition",
                            "transition",
                        )
                        if candidate.get(key)
                    },
                    "slide": index,
                }
            )
        arc = str(parsed.get("sequence_arc", "")).strip()
        return plan, arc
    except (ValueError, TypeError, json.JSONDecodeError, AttributeError) as exc:
        print(f"[VISUAL PLAN] Could not parse storyboard; using fallback plan: {exc}")
        return _fallback_visual_plan(slide_quotes, theme), (
            "A cohesive emotional progression from the opening thought to the conclusion."
        )

def _build_slide_prompt(
    *,
    slide_index: int,
    total_slides: int,
    slide_text: str,
    visual_plan: dict,
    sequence_arc: str,
    shared_style_block: str,
) -> str:
    """Combine shared art direction with the individual slide's visual brief."""
    role, role_guidance = get_slide_role(slide_index, total_slides)
    return f"""
Create slide {slide_index} of {total_slides} for an Instagram carousel.

CAROUSEL STORY ARC
{sequence_arc or "A cohesive emotional progression from opening to conclusion."}

SHARED VISUAL IDENTITY (follow on every slide)
{shared_style_block}

THIS SLIDE'S NARRATIVE ROLE
{role.upper()} — {role_guidance}
The storyboard's role label is: {visual_plan.get("role", role)}.
Emotion: {visual_plan.get("emotion", "emotion appropriate to the text")}.
Visual metaphor / scene: {visual_plan.get("visual_metaphor", "")}.
Composition: {visual_plan.get("composition", "")}.
Connection to the sequence: {visual_plan.get("transition", "")}.

EXACT QUOTE TO DISPLAY
{slide_text}

COMPOSITION AND OUTPUT RULES
- Create one complete, polished image, not a collage or a multi-panel layout.
- Make this slide visually distinct from the other slides while preserving the same
  subject identity, art direction, lighting logic, and color grading.
- Follow the visual metaphor and composition above; do not default to the same centered
  portrait or background for every slide.
- Keep the subject and important visual details clear at Instagram feed size.
- Leave generous top and bottom safe margins and enough uncluttered contrast for text.
- Place the supplied quote in bold, highly legible white sans-serif type, centered or
  carefully positioned according to the composition. Do not obscure the subject's face.
- {TYPOGRAPHY_CONSTRAINT}
- Do not add captions, labels, signatures, extra words, or decorative text.
""".strip()

def generate_multi_slide_carousel(
    theme: str = None, num_slides: int = 4
) -> tuple[list[str], list[str], str, str, str, list[str]]:
    """Generate carousel text and images with a shared style and content-aware storyboard."""
    if not isinstance(num_slides, int) or num_slides < 1:
        raise ValueError("num_slides must be a positive integer.")

    client = genai.Client()
    active_theme = theme if theme else get_random_theme()
    chosen_style = get_random_style()
    character_desc, subject_instruction = get_subject_and_instructions(active_theme)
    emotional_modifier = get_emotional_visual_modifier()

    # 1. Generate all slide text and accompanying post metadata.
    banned = ", ".join(f'"{phrase}"' for phrase in BANNED_PHRASES)
    text_prompt = f"""
You write Instagram carousel text for the account thisisdailywhisper. Theme: "{active_theme}".
 
VOICE: a quiet, perceptive friend talking to one person late at night. Warm, plain, specific.
Never a guru, never preachy, never a poster slogan. Use "you". Name small real-life moments
and objects (like a message left unsent) instead of abstract ideas. Short sentences.
The reader should think "how did it know?" and want to send it to someone.
 
Generate exactly {num_slides} short quote lines, separated by the pipe character | on one line:
- Slide 1: a scroll-stopping hook, at most 10 words. A specific, slightly uncomfortable truth
  or an unfinished thought that makes the reader need slide 2.
- Middle slides: develop the thought, one idea each, each pulling the reader forward.
- Last slide: land the thought with a feeling or a quiet reframe worth saving or sending.
Each line at most 22 words. Use simple, common English words and avoid spelling-prone words
where possible.
Never use these clichés or close variants: {banned}.
 
Also provide:
- A 2-3 sentence caption. Open with a hook in the reader's voice and end with a short
  question or an invitation to save or send it to someone.
- 5 relevant Instagram hashtags, including #thisisdailywhisper.
- A suggested song title and artist, followed by a short audio-genre/mood keyword.
Do not claim the song is trending or available unless you know that reliably.
 
Format exactly as:
QUOTE: <quote 1 | quote 2 | ...>
EXPLANATION: <caption>
HASHTAGS: <hashtags separated by spaces>
MUSIC: <song title - artist | genre/mood>
"""
    sentence_response = client.models.generate_content(
        model=TEXT_MODEL,
        contents=text_prompt,
    )
    raw_text = (sentence_response.text or "").strip()

    quote_raw = ""
    explanation = ""
    hashtags = "#thisisdailywhisper"
    music_recommendation = ""

    for line in raw_text.splitlines():
        if line.startswith("QUOTE:"):
            quote_raw = line.partition(":")[2].strip().replace('"', "")
        elif line.startswith("EXPLANATION:"):
            explanation = line.partition(":")[2].strip()
        elif line.startswith("HASHTAGS:"):
            hashtags = line.partition(":")[2].strip() or hashtags
        elif line.startswith("MUSIC:"):
            music_recommendation = line.partition(":")[2].strip()

    slide_quotes = [quote.strip() for quote in quote_raw.split("|") if quote.strip()]
    if len(slide_quotes) != num_slides:
        raise ValueError(
            f"Expected {num_slides} quotes, got {len(slide_quotes)}: {raw_text!r}"
        )

    # 2. Plan the entire sequence before rendering any image.
    visual_plan, sequence_arc = _generate_visual_plan(
        client, active_theme, slide_quotes
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("output") / "Carousel_Posts" / f"carousel_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    shared_style_block = build_carousel_style_block(
        chosen_style=chosen_style,
        emotional_modifier=emotional_modifier,
        character_desc=character_desc,
        subject_instruction=subject_instruction,
    )

    generated_image_paths = []
    generated_image_prompts = []
    first_slide_image = None

    # 3. Render each planned slide, using the first slide as a stable visual reference.
    for idx, slide_text in enumerate(slide_quotes, start=1):
        slide_plan = visual_plan[idx - 1]
        image_prompt = _build_slide_prompt(
            slide_index=idx,
            total_slides=num_slides,
            slide_text=slide_text,
            visual_plan=slide_plan,
            sequence_arc=sequence_arc,
            shared_style_block=shared_style_block,
        )
        generated_image_prompts.append(image_prompt)

        # The first image establishes the visual reference. Later images receive it
        # plus distinct slide directions, reducing style drift without copying layout.
        contents = [image_prompt] if idx == 1 else [first_slide_image, image_prompt]

        response = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(aspect_ratio=ASPECT_RATIO),
            ),
        )

        slide_path_jpg = output_dir / f"slide_{idx}_of_{num_slides}.jpg"
        image_saved = False

        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if not part.inline_data:
                    continue

                raw_image = Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
                if idx == 1:
                    # Preserve the original generated image as the reference, before
                    # resizing/compression, to avoid accumulating quality loss.
                    first_slide_image = raw_image.copy()

                raw_image = ImageOps.fit(
                    raw_image, (TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS
                )
                temp_path = output_dir / f"temp_slide_{idx}.jpg"
                raw_image.save(temp_path, "JPEG", quality=95)

                draw_quote_on_image(
                    image_path=str(temp_path),
                    quote=slide_text,
                    output_path=str(slide_path_jpg),
                    font_path="assets/Font/Montserrat-SemiBold.ttf",
                    font_size=52,
                    max_chars_per_line=28
                )
                temp_path.unlink(missing_ok=True)
                generated_image_paths.append(str(slide_path_jpg))
                image_saved = True
                break

        if not image_saved:
            raise RuntimeError(f"Failed to generate slide {idx} for carousel.")

    return (
        generated_image_paths,
        slide_quotes,
        explanation,
        hashtags,
        music_recommendation,
        generated_image_prompts,
    )