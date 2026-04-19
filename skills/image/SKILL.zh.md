---
name: "image"
description: "通过 ChatTool 调用多家模型服务，根据文本提示词生成 AI 图片。用户提到创建图片、生成插画、渲染场景，或使用 Flux、Stable Diffusion、Tongyi 等文生图模型时使用。"
version: 0.1.0
---

# Image Generation

根据文本提示词生成图片，支持 Pollinations、SiliconFlow、Tongyi、Hugging Face、Liblib 等多个平台。

## 工作流

1. 需要时先查看模型列表。
2. 使用选定平台执行 `generate "<prompt>"`。
3. 如果效果不理想，再调整提示词、模型、尺寸或风格。

## 各平台命令

### Pollinations（无需 API Key）
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

### Tongyi（阿里云）
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

## 配置

通过 `chatenv init` 或 `.env` 设置平台密钥：

| 平台 | 环境变量 |
| :--- | :--- |
| SiliconFlow | `SILICONFLOW_API_KEY` |
| Tongyi | `DASHSCOPE_API_KEY` |
| Hugging Face | `HUGGINGFACE_HUB_TOKEN` |
| Liblib | `LIBLIB_ACCESS_KEY` |
| Pollinations | `POLLINATIONS_API_KEY`（可选） |
