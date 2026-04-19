---
name: "image"
description: "Generate AI images from text prompts using multiple providers via ChatTool. Use when the user asks to create, generate, or draw an image, produce artwork, render a scene, or use text-to-image AI models like Flux, Stable Diffusion, or Tongyi."
version: 0.1.0
---

# Image Generation

Generate images from text prompts across multiple AI providers: Pollinations, SiliconFlow, Tongyi, Hugging Face, and Liblib.

## Workflow

1. **Check available models** (optional): run `list-models` for the chosen provider.
2. **Generate image**: run `generate "<prompt>"` with provider-specific options.
3. **Tune if needed**: adjust prompt, model, width/height, or style until quality is acceptable.

## Commands by Provider

### Pollinations (no API key required)
```bash
chattool image pollinations list-models
chattool image pollinations generate "a cyberpunk cat"
chattool image pollinations generate "a cyberpunk cat" --model turbo --width 512 --height 512
```

### SiliconFlow
```bash
chattool image siliconflow list-models
chattool image siliconflow generate "a cute dog"
chattool image siliconflow generate "a cute dog" --model "black-forest-labs/FLUX.1-schnell" --size "1024x1024"
```

### Tongyi (Alibaba)
```bash
chattool image tongyi generate "a cyberpunk cat on a rooftop" --style "<auto>" --size "1024*1024" -o cat_tongyi.png
```

### Hugging Face
```bash
chattool image huggingface generate "A futuristic city at night, neon lights" -o city_hf.png
```

### Liblib
```bash
chattool image liblib list-models
chattool image liblib generate "A cute dog" --model-id liblib-sdxl-model -o dog_liblib.png
```

## Configuration

Set provider API keys via `chatenv init` or a `.env` file:

| Provider | Environment Variable |
| :--- | :--- |
| SiliconFlow | `SILICONFLOW_API_KEY` |
| Tongyi | `DASHSCOPE_API_KEY` |
| Hugging Face | `HUGGINGFACE_HUB_TOKEN` |
| Liblib | `LIBLIB_ACCESS_KEY` |
| Pollinations | `POLLINATIONS_API_KEY` (optional) |
