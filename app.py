from pathlib import Path
import gradio as gr
from src.image_generator import generate_images_for_quote
from src.text_generator import generate_vibe_and_text

custom_css = """
.gradio-container, 
.gr-form, 
.form, 
.block.fieldset,
fieldset.block,
div[class*="block"],
div[class*="panel"] {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

label.span, .wrap label {
    color: inherit !important;
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
"""


def step1_generate_script(theme_selection, progress=gr.Progress()):
  """Step 1: Generates the quote and lines, then unhides the user approval row."""
  progress(0.3, desc=f"Generating {theme_selection} quote...")
  script_data = generate_vibe_and_text(selected_theme=theme_selection)

  theme = script_data.get("sub_genre", theme_selection)
  quote = script_data.get("inspiring_quote", "")
  sentences = script_data.get("sentences", [])

  formatted_quote = f"### Selected Theme: {theme_selection}\n"
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
      gr.update(visible=True),  # Unhide choice row
      gr.update(visible=False),  # Keep gallery hidden until images are generated
  )


def step2_generate_images(quote, sentences, progress=gr.Progress()):
  """Step 2: Takes the approved quote and generates 4 scene images using Imagen 3."""
  if not quote:
    return gr.update()

  progress(0.2, desc="Generating 4 narrative visual prompts...")
  progress(0.5, desc="Creating images via gemini-2.5-flash-image...")

  image_paths = generate_images_for_quote(quote, sentences)

  progress(1.0, desc="Done!")

  return gr.update(value=image_paths, visible=True)


with gr.Blocks(title="ETVibes Shorts Generator", css=custom_css) as demo:
  gr.Markdown("# 🎬 ETVibes Shorts Generator")
  gr.Markdown(
      "Select a theme to generate the script. Review the quote before"
      " proceeding to image generation."
  )

  # State variables to hold the generated quote between UI steps
  state_quote = gr.State("")
  state_sentences = gr.State([])

  with gr.Row():
    with gr.Column(scale=1):
      theme_radio = gr.Radio(
          choices=["INSPIRATIONAL_UPLIFTING", "LOVE_AND_ROMANCE"],
          value="INSPIRATIONAL_UPLIFTING",
          label="Select Theme",
          info="Choose the narrative direction for text generation",
      )
      generate_script_btn = gr.Button(
          "📝 Generate quote", elem_id="run-btn", size="sm"
      )

  with gr.Row():
    with gr.Column(scale=1):
      output_text = gr.Markdown(label="Generated Lines & Vibe")

      # Hidden Approval Row (Revealed only after quote generation)
      with gr.Row(visible=False) as approval_row:
        approve_btn = gr.Button(
            "✅ Continue to Images", elem_id="run-btn", size="sm"
        )
        regenerate_btn = gr.Button(
            "🔄 Generate New quote", elem_id="run-btn", size="sm"
        )

    with gr.Column(scale=2):
      output_gallery = gr.Gallery(
          label="Generated Scenes (9:16)",
          columns=4,
          rows=1,
          height="auto",
          object_fit="contain",
          visible=False,
      )

  # Step 1 Event Listeners
  generate_script_btn.click(
      fn=step1_generate_script,
      inputs=[theme_radio],
      outputs=[
          output_text,
          state_quote,
          state_sentences,
          approval_row,
          output_gallery,
      ],
  )

  regenerate_btn.click(
      fn=step1_generate_script,
      inputs=[theme_radio],
      outputs=[
          output_text,
          state_quote,
          state_sentences,
          approval_row,
          output_gallery,
      ],
  )

  # Step 2 Event Listener
  approve_btn.click(
      fn=step2_generate_images,
      inputs=[state_quote, state_sentences],
      outputs=[output_gallery],
  )

if __name__ == "__main__":
  demo.launch(inbrowser=True)