# 白嫖与低成本 AI 生图实战：ChatTool 全平台版

这篇文章给你一套可直接落地的 AI 生图方案，目标是：先跑起来、再控成本、最后稳定上线。

## 先说结论（按目标选）

- 想最快开跑：用 Pollinations.ai。
- 想低成本长期跑：用 SiliconFlow 免费模型。
- 想要阿里生态：用通义万相。
- 想用开源社区模型生态：用 Hugging Face。
- 想用国内平台生态和模型广场：用 LiblibAI。

## 平台全览（ChatTool 当前支持）

ChatTool 当前支持 5 个 image provider：

- `pollinations`
- `siliconflow`
- `tongyi`
- `huggingface`
- `liblib`

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
chatenv init -i -t pollinations -t siliconflow
```

你可以按需初始化全部图像配置：

```bash
chatenv init -i -t pollinations -t siliconflow -t tongyi -t huggingface -t liblib
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

- 下载失败优先看 HTTP 状态码（401/402 常见于鉴权和额度问题）。
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
