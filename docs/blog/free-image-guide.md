# AI 生图白嫖指南 ｜ 零成本玩转文生图

ChatTool 集成了市面上主流的 AI 生图 API，支持通过统一的命令行接口调用 Pollinations、SiliconFlow、通义万相、Hugging Face 和 LiblibAI 等服务。

本文主要介绍如何配置这些服务，以及各平台在免费额度、模型生态和适用场景上的差异，帮助你快速选择并接入合适的 AI 绘图能力。

注：这些平台都提供了免费额度，无需付费即可使用。

## 支持的平台

ChatTool 目前支持以下 5 个图像提供商（Image Provider）：

- **Pollinations.ai** (`pollinations`)：提供每周免费额度，适合快速验证和轻量级测试。
- **SiliconFlow (硅基流动)** (`siliconflow`)：提供丰富的开源模型，实名认证后包含大量免费模型。
- **Tongyi (通义万相)** (`tongyi`)：阿里云原生生态，适合国内企业级应用。
- **Hugging Face** (`huggingface`)：依托庞大的开源社区，拥有海量模型资源。
- **LiblibAI** (`liblib`)：国内领先的模型分享平台，风格多样，适合探索不同画风。

详细命令和参数总表见 [AI 绘图工具开发者指南](../tools/image.md)。

## 成本与门槛对比

### Pollinations.ai

- 账户 API 需要 `POLLINATIONS_API_KEY`。
- 每个账户每周有 1.5 Pollen 免费额度。
- 文生图 endpoint：`https://gen.pollinations.ai/image/{prompt}`。
- 适合快速测试、做轻量演示。

### SiliconFlow（硅基流动）

- 需要 `SILICONFLOW_API_KEY`。
- 实名后可使用全部免费模型，免费模型调用消耗为 0。
- 免费模型有固定 Rate Limits。
- 平台同时有免费版与收费版，收费版一般带 `Pro/` 前缀。

### 通义万相（Tongyi）

- 需要 `DASHSCOPE_API_KEY`。
- 更偏企业和生产调用场景，阿里云生态集成方便。
- 成本取决于 DashScope 计费策略与活动配额。

### Hugging Face

- 需要 `HUGGINGFACE_HUB_TOKEN`。
- 模型生态丰富，适合快速试多种开源模型。
- 成本和限额取决于所用推理服务与账户策略。

### LiblibAI

- 需要 `LIBLIB_ACCESS_KEY` + `LIBLIB_SECRET_KEY`。
- 适合使用 Liblib 平台模型生态与工作流。
- 成本取决于平台策略与所选模型。

## 3 分钟上手

## 1）安装

```bash
pip install "chattool[images]"
```

## 2）配置

```bash
chatenv init -t pollinations -t siliconflow
```

你可以按需初始化全部图像配置：

```bash
❯ chatenv init
Starting interactive configuration...
Select a category to configure:
> Image
[Image] Select a provider to configure:
> Tongyi Wanxiang Configuration (tongyi, dashscope)
  Hugging Face Configuration (hf, huggingface)
  Pollinations Configuration (pollinations, poll)
  LiblibAI Configuration (liblib)
  ----
  Back
```

低成本起步至少配置：

- `POLLINATIONS_API_KEY`
- `SILICONFLOW_API_KEY`

可选配置：

- `POLLINATIONS_MODEL_ID`（默认 `flux`）
- `SILICONFLOW_MODEL_ID`（默认 `black-forest-labs/FLUX.1-schnell`）

## 3）列模型 + 生成（全平台）

```bash
# Pollinations
chattool image pollinations list-models
chattool image pollinations generate "a cat in space" -o cat.png

# SiliconFlow
chattool image siliconflow list-models
chattool image siliconflow generate "a cyberpunk city at night" -o city.png

# Tongyi
chattool image tongyi generate "一只在屋顶晒太阳的赛博朋克猫" --style "<auto>" --size "1024*1024" -o tongyi.png

# Hugging Face
chattool image huggingface generate "A futuristic city at night, neon lights" -o hf.png

# LiblibAI
chattool image liblib list-models
chattool image liblib generate "A cute dog" --model-id liblib-sdxl-model -o liblib.png
```

## 避坑清单

- Pollinations 的免费额度是按周重置，不是一次性总额度。
- SiliconFlow 选模型时注意 `Pro/` 前缀，避免误用收费模型。
- Tongyi / Hugging Face / LiblibAI 的可用额度与计费以平台账户策略为准。
- 生产场景建议先在 `list-models` 里固定模型 ID，再放量调用。

## 推荐实践

- 开发联调用 Pollinations 或 Hugging Face，快速验证提示词效果。
- 成本敏感的长期任务优先 SiliconFlow 免费模型。
- 有特定平台要求时再切 Tongyi 或 LiblibAI。
- 在 `.env` 固定默认模型，避免每次命令都手写长模型名。

## 参考

- Pollinations API: `https://enter.pollinations.ai/api/docs`
- SiliconFlow Rate Limits: `https://docs.siliconflow.cn/cn/userguide/rate-limits/rate-limit-and-upgradation`
