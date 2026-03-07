---
name: "image"
description: "使用 ChatTool 调用多平台 AI 生图能力（Pollinations、SiliconFlow、Tongyi、Hugging Face、Liblib）。"
---

# Image 生图助手

该技能用于统一处理 AI 图片生成任务，支持多平台模型查询与出图。

## 能力

- **列出模型**：查看指定平台可用文生图模型。
- **生成图片**：根据提示词生成图片，并按平台能力设置尺寸/模型参数。
- **平台切换**：在不同平台之间选择更合适的成本、速度和风格。

## 常用命令

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

- `chattool image tongyi generate "一只在屋顶晒太阳的赛博朋克猫" --style "<auto>" --size "1024*1024" -o cat_tongyi.png`

### Hugging Face

- `chattool image huggingface generate "A futuristic city at night, neon lights" -o city_hf.png`

## 配置要求

请先通过 `chatenv init` 或 `.env` 配置对应平台密钥（如 `DASHSCOPE_API_KEY`、`HUGGINGFACE_HUB_TOKEN`、`LIBLIB_ACCESS_KEY`、`POLLINATIONS_API_KEY`、`SILICONFLOW_API_KEY`）。

## 使用建议

- 先用 `list-models` 确认模型可用性，再进行生成。
- 若结果不理想，优先调整提示词、模型和尺寸，而不是直接更换平台。
