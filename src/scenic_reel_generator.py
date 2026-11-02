"""===============================================================================
Module: scenic_reel_generator.py
Description: Generates 'Know Thyself' style scenic reels featuring an epic world
             landscape, profound philosophical life lessons, progressive word-by-word
             or sentence-by-sentence subtitle overlays, and synchronized voiceover/audio.
==============================================================================="""
import asyncio
import io
import json
import logging
import re
import subprocess
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image, ImageOps, ImageDraw, ImageFont
import textwrap

from .config import REEL_DIR, FONTS_DIR
from .prompt_config import TARGET_WIDTH, TARGET_HEIGHT, ASPECT_RATIO, TEXT_MODEL, IMAGE_MODEL
from .Publish_IG_Post import resolve_and_fetch_audio

logger = logging.getLogger("ScenicReelGenerator")

"""===============================================================================
    Generates a single-slide epic scenic reel with a profound life lesson,
    progressive text overlays, cloned voiceover, and background music.

    Args:
        theme (str, optional): Theme focus for the life lesson. Defaults to "consciousness and self-discovery".
        with_voiceover (bool, optional): Whether to synthesize voiceover audio. Defaults to True.

    Returns:
        tuple[str, str, str, str, str, str]: File path to final reel, headline text, 
                                             explanation caption, hashtags, music recommendation, 
                                             and image generation prompt.
==============================================================================="""
def generate_scenic_reel(theme: str = "consciousness and self-discovery", with_voiceover: bool = True) -> tuple[str, str, str, str, str, str]:
    client = genai.Client()
    output_dir = Path("output") / "ScenicReel"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"[SCENIC REEL] Starting generation for theme: '{theme}'")

    # =========================================================================
    # STEP 1: Generate Philosophical Life Lesson & Image Prompt via Gemini
    # =========================================================================
    content_prompt = f"""
You are the creator of profound, philosophical, and reflective Instagram reels for 'Know Thyself' style accounts.
Theme/Focus: "{theme}"

Requirements:
1. Write a profound, deeply insightful multi-sentence life lesson paragraph (about 3 to 4 sentences long) exploring consciousness, inner truth, self-discovery, or personal transformation. Keep it resonant and wise.
2. Write a detailed visual prompt for an image generation model (`gemini-2.5-flash-image`) depicting a breathtaking, epic scenic view of a majestic natural wonder somewhere in the world (e.g., sweeping mountain peaks, serene alpine lake, vast misty valley). It must be vertical ({TARGET_WIDTH}x{TARGET_HEIGHT}), hyper-realistic, pristine detail, and have a clear, uncluttered middle/upper area so text can be overlaid later. Do NOT include any text inside the image prompt.
3. Provide a 2-3 sentence Instagram caption opening with a relatable hook and ending with a reflective question.
4. Provide 5 relevant Instagram hashtags including #knowthyself.
5. Provide a suggested song title and artist, followed by a short audio-genre/mood keyword.

Format your output strictly as:
LESSON: <the full multi-sentence life lesson paragraph>
IMAGE_PROMPT: <detailed image generation prompt>
EXPLANATION: <caption text>
HASHTAGS: <hashtags separated by spaces>
MUSIC: <song title - artist | genre/mood>
"""

    logger.info("[SCENIC REEL] Requesting life lesson and scenic image prompt from Gemini...")
    response = client.models.generate_content(
        model=TEXT_MODEL,
        contents=content_prompt,
    )
    raw_text = (response.text or "").strip()

    lesson_text = ""
    image_prompt = ""
    explanation = ""
    hashtags = "#knowthyself"
    music_recommendation = ""

    for line in raw_text.splitlines():
        if line.startswith("LESSON:"):
            lesson_text = line.partition(":")[2].strip().replace('"', "")
        elif line.startswith("IMAGE_PROMPT:"):
            image_prompt = line.partition(":")[2].strip()
        elif line.startswith("EXPLANATION:"):
            explanation = line.partition(":")[2].strip()
        elif line.startswith("HASHTAGS:"):
            hashtags = line.partition(":")[2].strip() or hashtags
        elif line.startswith("MUSIC:"):
            music_recommendation = line.partition(":")[2].strip()

    if not lesson_text or not image_prompt:
        logger.error(f"❌ [SCENIC REEL ERROR] Failed to parse Gemini response: {raw_text}")
        raise RuntimeError("Failed to generate scenic reel content payload.")

    logger.info(f"  └─ Lesson generated: {lesson_text[:60]}...")

    # =========================================================================
    # STEP 2: Generate Epic Scenic Background Image via Gemini
    # =========================================================================
    logger.info("[SCENIC REEL] Generating epic scenic background image...")
    img_response = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=[image_prompt],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio=ASPECT_RATIO),
        ),
    )

    base_image_path = output_dir / "scenic_background.jpg"
    image_saved = False

    if img_response.candidates and img_response.candidates[0].content.parts:
        for part in img_response.candidates[0].content.parts:
            if not part.inline_data:
                continue
            raw_image = Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
            raw_image = ImageOps.fit(raw_image, (TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)
            raw_image.save(base_image_path, "JPEG", quality=95)
            image_saved = True
            break

    if not image_saved:
        raise RuntimeError("Failed to render scenic background image from Gemini.")
    logger.info(f"  └─ Scenic background saved to {base_image_path}")

    # =========================================================================
    # STEP 3: Generate Voiceover & Split Sentences for Progressive Display
    # =========================================================================
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', lesson_text) if s.strip()]
    if not sentences:
        sentences = [lesson_text]

    audio_clips_dir = output_dir / "individual_audio_clips"
    audio_clips_dir.mkdir(parents=True, exist_ok=True)
    
    sentence_audio_paths = []
    sentence_durations = []

    if with_voiceover:
        from TTS.api import TTS
        import torch
        
        reference_audio_path = Path("assets/voice_reference_female.mp3")
        if not reference_audio_path.exists():
            raise FileNotFoundError(f"Reference voice asset required at {reference_audio_path}")

        logger.info("[SCENIC REEL] Initializing local XTTS v2 model for voiceover narration...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

        for idx, sentence in enumerate(sentences, start=1):
            clip_path = audio_clips_dir / f"sentence_{idx}_voice.wav"
            try:
                tts.tts_to_file(
                    text=sentence,
                    file_path=str(clip_path),
                    speaker_wav=str(reference_audio_path),
                    language="en"
                )
            except Exception as e:
                raise RuntimeError(f"Voice cloning failed on sentence {idx}: {e}")

            sentence_audio_paths.append(str(clip_path))
            
            # Get exact duration using ffprobe
            dur_res = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(clip_path)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
            )
            sentence_durations.append(float(dur_res.stdout.strip()))

        # Concatenate audio sentence clips into a single voiceover file
        concat_txt = audio_clips_dir / "audio_concat.txt"
        with open(concat_txt, "w") as f:
            for p in sentence_audio_paths:
                f.write(f"file '{Path(p).name}'\n")

        voiceover_path = output_dir / "voiceover.wav"
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "audio_concat.txt",
            "-c:a", "pcm_s16le", str(voiceover_path.resolve())
        ], cwd=audio_clips_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    else:
        sentence_durations = [4.0] * len(sentences)
        voiceover_path = None

    # =========================================================================
    # STEP 4: Progressive Subtitle Video Compositing & Final Compilation
    # =========================================================================
    logger.info("[SCENIC REEL] Rendering progressive subtitle frames and compiling base video...")
    
    video_clips_dir = output_dir / "video_segments"
    video_clips_dir.mkdir(parents=True, exist_ok=True)
    
    base_img = Image.open(base_image_path).convert("RGB")
    font_path = FONTS_DIR / "Roboto-Bold.ttf"
    if not font_path.exists():
        font_path = FONTS_DIR / "DejaVuSans-Bold.ttf"
        if not font_path.exists():
            font_path = None

    try:
        font = ImageFont.truetype(str(font_path), 52) if font_path else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    segment_video_paths = []

    # Render a video segment for each sentence showing accumulated text up to that sentence
    accumulated_text = ""
    for idx, (sentence, duration) in enumerate(zip(sentences, sentence_durations), start=1):
        accumulated_text = f"{accumulated_text} {sentence}".strip()
        
        # Draw text onto a copy of the base image
        frame_img = base_img.copy()
        draw = ImageDraw.Draw(frame_img)
        
        # Wrap text nicely for vertical 1080x1920 layout
        margin = 100
        max_width = TARGET_WIDTH - (margin * 2)
        wrapped_lines = []
        for paragraph in accumulated_text.split("\n"):
            wrapped_lines.extend(textwrap.wrap(paragraph, width=32))
            
        # Calculate total text block height to center vertically in the upper/middle area
        line_height = 65
        total_text_height = len(wrapped_lines) * line_height
        y_text = (TARGET_HEIGHT // 2) - (total_text_height // 2) - 100

        for line in wrapped_lines:
            # Get bounding box for horizontal centering
            bbox = draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            x_text = (TARGET_WIDTH - w) // 2
            
            # Draw dark drop shadow for cinematic readability
            draw.text((x_text + 3, y_text + 3), line, font=font, fill=(0, 0, 0))
            draw.text((x_text, y_text), line, font=font, fill=(255, 255, 255))
            y_text += line_height

        segment_img_path = video_clips_dir / f"segment_{idx}.jpg"
        frame_img.save(segment_img_path, "JPEG", quality=95)

        # Create video clip with MoviePy using exact audio clip duration
        clip_audio_path = audio_clips_dir / f"sentence_{idx}_voice.wav"
        img_clip = ImageClip(str(segment_img_path)).with_duration(duration)
        
        if with_voiceover and clip_audio_path.exists():
            from moviepy import AudioFileClip
            audio_clip = AudioFileClip(str(clip_audio_path))
            img_clip = img_clip.with_audio(audio_clip)

        segment_video_paths.append(img_clip)

    # Concatenate all video segments together
    final_video_base = concatenate_videoclips(segment_video_paths, method="compose")
    base_reel_output = output_dir / "base_scenic_reel.mp4"
    
    final_video_base.write_videofile(
        str(base_reel_output),
        fps=24,
        codec="libx264",
        audio_codec="aac" if with_voiceover else None,
        preset="medium",
        logger=None
    )

    # =========================================================================
    # STEP 5: Mix Background Music & Final Output Generation
    # =========================================================================
    logger.info("[SCENIC REEL] Mixing background music track...")
    final_reel_path = REEL_DIR / "generated_reel.mp4"
    REEL_DIR.mkdir(parents=True, exist_ok=True)

    # Resolve and mix music track if available
    music_file = resolve_and_fetch_audio(music_recommendation)
    if music_file and Path(music_file).exists():
        try:
            # Use ffmpeg to mix voiceover with background music at lower volume
            cmd = [
                "ffmpeg", "-y",
                "-i", str(base_reel_output),
                "-i", str(music_file),
                "-filter_complex", "[1:a]volume=0.25[music];[0:a][music]amix=inputs=2:duration=first[a]",
                "-map", "0:v", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac",
                str(final_reel_path)
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except Exception as e:
            logger.warning(f"⚠️ Music mixing failed ({e}), falling back to base reel audio.")
            shutil.copy(base_reel_output, final_reel_path)
    else:
        shutil.copy(base_reel_output, final_reel_path)

    logger.info(f"🎉 [SCENIC REEL SUCCESS] Final Reel ready at: {final_reel_path}")

    # Return full required tuple payload
    return (
        str(final_reel_path),
        lesson_text,
        explanation,
        hashtags,
        music_recommendation,
        image_prompt
    )