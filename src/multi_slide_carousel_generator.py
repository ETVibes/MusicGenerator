"""===============================================================================
Module: multi_slide_carousel_generator.py
Description: Generates Instagram carousel text and a coordinated set of images.
==============================================================================="""

from datetime import datetime
import io
import json
import re
from pathlib import Path
import subprocess

from google import genai
from google.genai import types
from PIL import Image, ImageOps

from .prompt_config import (
    ASPECT_RATIO,
    TARGET_HEIGHT,
    TARGET_WIDTH,
    SLIDE_ROLE_GUIDANCE,
    POSE_CONSTRAINT,
    draw_quote_on_image,
    get_random_theme,
    get_subject_and_instructions,
    get_text_prompt_segments_by_theme,
    get_style_and_modifier_for_theme,
)

TEXT_MODEL = VOICEOVER_MODEL = "gemini-3.6-flash"
IMAGE_MODEL = "gemini-2.5-flash-image"

def get_slide_role(index: int, total: int) -> tuple[str, str]:
    """Return the narrative role and role guidance for a slide at a given position."""
    if index <= 1:
        key = "opening"
    elif index >= total:
        key = "resolution"
    elif index == 2:
        key = "development"
    else:
        key = "realization"

    return key, SLIDE_ROLE_GUIDANCE[key]

def build_carousel_style_block(
    chosen_style: str,
    emotional_modifier: str,
    character_desc: str,
    subject_instruction: str,
) -> str:
    """Build the shared visual identity reused in every slide prompt."""
    return f"""
SHARED CAROUSEL VISUAL IDENTITY
- Art direction: {chosen_style}
- Lighting and atmosphere: {emotional_modifier}
- Main subject: {character_desc}
- Subject continuity: {subject_instruction}
- Keep the same overall color grading, contrast, lighting logic, rendering medium,
  and level of realism throughout all slides.
- Use a vertical {TARGET_WIDTH}x{TARGET_HEIGHT} canvas ({ASPECT_RATIO}).
- The mood must feel warm, hopeful and calm even when the quote is bittersweet; shadows stay soft and lifted.
- {POSE_CONSTRAINT}
- Avoid watermarks, logos, borders, collages, split panels, and unrelated background text.
""".strip()

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

COMPOSITION AND OUTPUT RULES
- Create one complete, polished image, not a collage or a multi-panel layout.
- Make this slide visually distinct from the other slides while preserving the same
  subject identity, art direction, lighting logic, and color grading.
- Follow the visual metaphor and composition above; do not default to the same centered
  portrait or background for every slide.
- Keep the subject and important visual details clear at Instagram feed size.
- **Do not render any text, letters, or quotes inside the image.** Leave the middle and upper areas clean and uncluttered so text can be overlaid later.
- Avoid watermarks, logos, borders, collages, split panels, and unrelated background text.
""".strip()

def generate_voiceover(
    slide_quotes: list[str], 
    output_path: str = "output/voiceover.mp3", 
    voice_name: str = "alloy"
) -> str:
    """
    Generates a continuous text-to-speech voiceover audio file reading the slide quotes 
    using the Gemini TTS API, and saves it to disk.
    """
    client = genai.Client()
    
    script = ". ".join(quote.strip() for quote in slide_quotes) + "."
    tts_prompt = f"Read the following text aloud in a calm, warm, conversational, and steady tone suitable for a cinematic lifestyle reel: {script}"
    
    response = client.models.generate_content(
        model=VOICEOVER_MODEL,
        contents=tts_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name
                    )
                )
            )
        )
    )
    
    audio_saved = False
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                with open(output_file, "wb") as f:
                    f.write(part.inline_data.data)
                audio_saved = True
                break
                
    if not audio_saved:
        raise RuntimeError("Failed to generate voiceover audio stream.")
        
    return str(output_file)

def add_background_music_and_voiceover(
    video_path: str,
    voiceover_path: str,
    music_path: str,
    output_path: str,
    voiceover_volume: float = 1.0,
    music_volume: float = 0.15,
) -> str:
    """
    Mixes a text-to-speech voiceover track and a background music track directly into 
    the final video using FFmpeg, applying audio ducking so the voice remains prominent.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", voiceover_path,
        "-i", music_path,
        "-filter_complex",
        f"[1:a]volume={voiceover_volume}[vo];"
        f"[2:a]volume={music_volume}[bg];"
        f"[vo][bg]amix=inputs=2:duration=first:dropout_transition=2[a:mix]",
        "-map", "0:v:0",
        "-map", "[a:mix]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        str(output_file)
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio mixing failed:\n{result.stderr}")

    return str(output_file)
    
def generate_multi_slide_carousel(
    theme: str = None, num_slides: int = 4, background_music_path: str = None
) -> tuple[str, list[str], str, str, str, list[str]]:
    """Generate carousel text and images with a shared style and content-aware storyboard."""
    if not isinstance(num_slides, int) or num_slides < 1:
        raise ValueError("num_slides must be a positive integer.")

    client = genai.Client()
    active_theme = theme if theme else get_random_theme()
    chosen_style, emotional_modifier = get_style_and_modifier_for_theme(active_theme)
    character_desc, subject_instruction = get_subject_and_instructions(active_theme)
    feel, voice, slide_one, mid_slides, last_slide, ban = get_text_prompt_segments_by_theme(active_theme)

    # 1. Generate all slide text and accompanying post metadata.
    text_prompt = f"""
You write {feel} Instagram carousel text for the account thisisdailywhisper. Theme: "{active_theme}".
 
VOICE: {voice}
 
Generate exactly {num_slides} short quote lines, separated by the pipe character | on one line:
- Slide 1: {slide_one}
- Middle slides: {mid_slides}
- Last slide (Must act as a share trigger or direct prompt to send to someone special): {last_slide}
Each line at most 20 words. Keep it entirely {feel}.
{ban}.
 
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

    # 4. Generate Voiceover & Compile into Reel with Background Audio
    voiceover_path = generate_voiceover(slide_quotes, output_path=str(output_dir / "voiceover.mp3"))
    
    base_video_path = str(output_dir / "base_reel.mp4")
    image_list_txt = output_dir / "images.txt"
    with open(image_list_txt, "w") as f:
        for img_path in generated_image_paths:
            f.write(f"file '{Path(img_path).name}'\nduration 3\n")
        if generated_image_paths:
            f.write(f"file '{Path(generated_image_paths[-1]).name}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "images.txt",
        "-vsync", "vfr", "-pix_fmt", "yuv420p", "-r", "30", base_video_path
    ], cwd=output_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    final_reel_path = str(output_dir / "final_reel_with_audio.mp4")
    
    if background_music_path and Path(background_music_path).exists():
        add_background_music_and_voiceover(
            video_path=base_video_path,
            voiceover_path=voiceover_path,
            music_path=background_music_path,
            output_path=final_reel_path
        )
    else:
        subprocess.run([
            "ffmpeg", "-y", "-i", base_video_path, "-i", voiceover_path,
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
            "-pix_fmt", "yuv420p", final_reel_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return (
        final_reel_path,
        slide_quotes,
        explanation,
        hashtags,
        music_recommendation,
        generated_image_prompts,
    )