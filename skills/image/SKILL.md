---
name: "image"
description: "Use ChatTool to generate AI images across Pollinations, SiliconFlow, Tongyi, Hugging Face, and Liblib."
---

# Image Generation Assistant

This skill provides a unified workflow for text-to-image generation with multiple providers.

## Capabilities

- **List Models**: Inspect available text-to-image models by provider.
- **Generate Images**: Produce images from prompts with provider-specific options.
- **Switch Providers**: Choose platforms by cost, speed, or model style.

## Common Commands

### Pollinations

- `chattool image pollinations list-models`
- `chattool image pollinations generate "a cyberpunk cat"`
- `chattool image pollinations generate "a cyberpunk cat" --model turbo --width 512 --height 512`

### SiliconFlow

- `chattool image siliconflow list-models`
- `chattool image siliconflow generate "a cute dog"`
- `chattool image siliconflow generate "a cute dog" --model "black-forest-labs/FLUX.1-schnell" --size "1024x1024"`

### Liblib

- `chattool image liblib list-models`
- `chattool image liblib generate "A cute dog" --model-id liblib-sdxl-model -o dog_liblib.png`

### Tongyi

- `chattool image tongyi generate "a cyberpunk cat on a rooftop" --style "<auto>" --size "1024*1024" -o cat_tongyi.png`

### Hugging Face

- `chattool image huggingface generate "A futuristic city at night, neon lights" -o city_hf.png`

## Configuration

Configure provider keys first via `chatenv init` or `.env` (for example: `DASHSCOPE_API_KEY`, `HUGGINGFACE_HUB_TOKEN`, `LIBLIB_ACCESS_KEY`, `POLLINATIONS_API_KEY`, `SILICONFLOW_API_KEY`).

## Usage Tips

- Use `list-models` before generation to verify model availability.
- Tune prompt, model, and image size first when quality is not ideal.
