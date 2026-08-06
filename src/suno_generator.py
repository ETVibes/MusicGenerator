import os
import time
import requests


def generate_suno_audio(suno_prompt, title, output_dir="outputs"):
  suno_key = os.getenv("SUNO_API_KEY")
  suno_url = os.getenv("SUNO_BASE_URL", "https://api.musicapi.ai/api/v1").rstrip(
      "/"
  )

  headers = {
      "Authorization": f"Bearer {suno_key}",
      "Content-Type": "application/json",
  }

  payload = {
      "task_type": "create_music",
      "custom_mode": True,
      "make_instrumental": True,
      "prompt": suno_prompt,
      "tags": suno_prompt,
      "title": title,
      "mv": "sonic-v4",
  }

  print(f"--> Sending request to Suno for: '{title}'...")
  response = requests.post(
      f"{suno_url}/sonic/create", json=payload, headers=headers
  )

  if response.status_code == 404:
    response = requests.post(
        f"{suno_url}/suno/create", json=payload, headers=headers
    )

  response.raise_for_status()

  task_data = response.json()
  task_id = (
      task_data.get("task_id")
      or task_data.get("id")
      or task_data.get("data", {}).get("task_id")
  )

  print(f"--> Generation task created (ID: {task_id}). Polling for audio...")

  audio_url = None
  clip_id = None
  max_attempts = 30

  for attempt in range(1, max_attempts + 1):
    time.sleep(10)
    status_res = requests.get(f"{suno_url}/task/{task_id}", headers=headers)

    if status_res.status_code == 200:
      res_json = status_res.json()
      status = res_json.get("status") or res_json.get("data", {}).get("status")

      if status in ["SUCCESS", "completed", "TEXT_SUCCESS"]:
        data_block = res_json.get("data", res_json)

        if isinstance(data_block, list) and len(data_block) > 0:
          audio_url = data_block[0].get("audio_url")
          clip_id = data_block[0].get("id") or data_block[0].get("clip_id")
        elif isinstance(data_block, dict):
          audio_url = data_block.get("audio_url") or data_block.get(
              "audio_path"
          )
          clip_id = data_block.get("id") or data_block.get("clip_id")

        print("--> Base audio rendering complete!")
        break
      elif status in ["FAILED", "REJECTED"]:
        raise Exception("Suno audio generation failed on the server.")
      else:
        print(f"    [Polling {attempt}/{max_attempts}] Processing...")

  if not audio_url:
    raise TimeoutError("Suno generation timed out.")

  # --- Export Lossless WAV ---
    target_download_url = audio_url
    if clip_id:
      print("--> Exporting lossless WAV file...")
      wav_res = requests.post(
          f"{suno_url}/sonic/wav", json={"clip_id": clip_id}, headers=headers
      )
      if wav_res.status_code == 200:
        wav_json = wav_res.json()
        wav_url = (
            wav_json.get("data", {}).get("wav_url")
            or wav_json.get("wav_url")
            or wav_json.get("audio_url")
        )
        if wav_url:
          target_download_url = wav_url
          print("--> WAV export ready!")
        else:
          print(
              "--> Could not obtain WAV link from response, falling back to base"
              " audio URL."
          )
      else:
        print(
            f"--> Lossless WAV endpoint returned status {wav_res.status_code},"
            " falling back to base audio URL."
        )

  os.makedirs(output_dir, exist_ok=True)
  output_path = os.path.join(output_dir, "relaxation_audio_35s.wav")

  audio_bytes = requests.get(target_download_url).content
  with open(output_path, "wb") as f:
    f.write(audio_bytes)

  return output_path