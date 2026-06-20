# AI 绘图工具开发者指南

ChatTool 已集成多个主流 AI 绘图工具的 API 调用，支持命令行 (CLI) 和 Python 代码两种调用方式。

## 安装依赖

```bash
pip install "chattool[images]"
```

## 支持平台

| 平台 | Provider ID | 环境变量 | 说明 |
| :--- | :--- | :--- | :--- |
| **通义万相** | `tongyi` | `DASHSCOPE_API_KEY` | [阿里云 DashScope](https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-wanxiang-api-details) |
| **Hugging Face** | `huggingface` | `HUGGINGFACE_HUB_TOKEN` | [Inference API](https://huggingface.co/docs/api-inference/detailed_parameters#text-to-image) |
| **LiblibAI** | `liblib` | `LIBLIB_ACCESS_KEY`, `LIBLIB_SECRET_KEY` | [Liblib API](https://liblibai.feishu.cn/wiki/UAMVw67NcifQHukf8fpccgS5n6d) |
| **Pollinations.ai** | `pollinations` | `POLLINATIONS_API_KEY`, `POLLINATIONS_MODEL_ID`(可选) | [Pollinations API](https://enter.pollinations.ai/api/docs) |
| **SiliconFlow** | `siliconflow` | `SILICONFLOW_API_KEY`, `SILICONFLOW_MODEL_ID` | [SiliconFlow API](https://docs.siliconflow.cn/) |
| **OpenAI OAuth 生图** | `codex` | `OPENAI_ACCESS_TOKEN`、`OPENAI_REFRESH_TOKEN`；可选 `OPENAI_ACCESS_TOKEN_EXPIRES_AT`、`OPENAI_API_BASE`、`OPENAI_API_MODEL`、`OPENAI_IMAGE_MODEL` | OpenAI/ChatGPT OAuth `responses` + `gpt-image-2` 桥接 |

### 选型建议（按目标）

*   快速开跑：Pollinations.ai
*   低成本长期调用：SiliconFlow 免费模型
*   阿里云生态：通义万相
*   开源模型生态：Hugging Face
*   国内模型平台生态：LiblibAI
*   已有 OpenAI OAuth token：OpenAI OAuth 生图

另见博客：[白嫖与低成本 AI 生图实战：ChatTool 全平台版](../blog/free-image-guide.md)。

## 1. 配置环境变量

使用 `chatenv` 命令初始化配置：

```bash
# 查看支持的配置类型
chatenv init --help

# 交互式设置 Key
chatenv init -i -t pollinations -t siliconflow
```

或者直接编辑 `.env` 文件。

### SiliconFlow (硅基流动) 说明

SiliconFlow 提供免费和付费模型。

*   **免费模型**：实名认证后可使用全部免费模型。免费模型调用费用为 0。
*   **Rate Limits**：免费模型有固定的速率限制。详情请参考 [SiliconFlow Rate Limits](https://docs.siliconflow.cn/cn/userguide/rate-limits/rate-limit-and-upgradation)。
*   **模型区分**：免费版按原名称命名（如 `black-forest-labs/FLUX.1-schnell`），收费版通常有 `Pro/` 前缀。

## 2. 命令行使用 (CLI)

### Pollinations.ai 说明

Pollinations.ai 账户 API 需要密钥，免费额度为每个账户每周 1.5 Pollen（无需信用卡）。

*   API 文档入口：`https://enter.pollinations.ai/api/docs`
*   图片 endpoint：`https://gen.pollinations.ai/image/{prompt}`
*   需要配置：`POLLINATIONS_API_KEY`
*   默认模型配置项：`POLLINATIONS_MODEL_ID`（默认 `flux`）

### Pollinations.ai 命令

```bash
# 查看文生图模型列表
chattool image pollinations list-models

# 默认使用 flux 模型
chattool image pollinations generate "a cyberpunk cat"

# 指定模型和尺寸
chattool image pollinations generate "a cyberpunk cat" --model turbo --width 512 --height 512
```

### OpenAI OAuth 生图说明

`codex` provider 走 OpenAI/ChatGPT OAuth access token，不会读取 Hermes 的本地登录文件。长期配置统一放在 OpenAI/OAI chatenv 下：

*   `OPENAI_ACCESS_TOKEN`：OAuth access token，用于发起 OAuth-backed image 请求。
*   `OPENAI_REFRESH_TOKEN`：OAuth refresh token，用于在 access token 过期前/过期后向 OpenAI OAuth token endpoint 换取新的 access token。
*   `OPENAI_ACCESS_TOKEN_EXPIRES_AT`：access token 过期时间（UTC ISO）；这是当前唯一需要持久化的 token 日期字段。`codex` provider 会在使用前读取它，发现过期时优先用 `OPENAI_REFRESH_TOKEN` 自动刷新。
*   `OPENAI_API_BASE`：OpenAI/OAI API base，可用于覆盖默认 backend。
*   `OPENAI_API_MODEL`：host model，用于 responses 调用中驱动 `image_generation` tool。
*   `OPENAI_IMAGE_MODEL`：默认图片模型 preset，例如 `gpt-image-2-medium`。

`--aspect-ratio`、`--timeout`、`--host-model`、`--base-url` 等是命令/调用级临时参数，不再作为独立 Codex chatenv 配置管理。

### OpenAI OAuth 生图命令

```bash
# 查看内置图片模型 preset
chattool image codex list-models

# 生成图片；未传 -o 时默认写到 ./generated/image_codex_<model>_<timestamp>.png
chattool image codex generate "a cinematic fox in the snow"

# 指定纵横比、图片质量档位与输出路径
chattool image codex generate "a cinematic fox in the snow" \
  --aspect-ratio portrait \
  --image-model gpt-image-2-high \
  -o fox_codex.png
```

### SiliconFlow

```bash
# 查看文生图模型列表
chattool image siliconflow list-models

# 生成图片
chattool image siliconflow generate "a cute dog"

# 指定模型和尺寸
chattool image siliconflow generate "a cute dog" --model "black-forest-labs/FLUX.1-schnell" --size "1024x1024"
```

### LiblibAI

```bash
# 查看模型
chattool image liblib list-models

# 生成图片（可选 --model-id）
chattool image liblib generate "A cute dog" --model-id liblib-sdxl-model -o dog_liblib.png
```

### Tongyi Wanxiang

```bash
chattool image tongyi generate "一只在屋顶晒太阳的赛博朋克猫" --style "<auto>" --size "1024*1024" -o cat_tongyi.png
```

### Hugging Face

```bash
chattool image huggingface generate "A futuristic city at night, neon lights" -o city_hf.png
```

若未传 `-o/--output`，`huggingface` 与 `codex` 这类直接返回 PNG bytes 的 provider，会默认写入：

```text
./generated/image_<provider>_<model>_<timestamp>.png
```

不同 Provider 的参数不完全相同，请以对应子命令 `--help` 为准。

## 3. Python 代码调用

您也可以在 Python 项目中直接导入使用：

```python
from chattool.tools.image import create_generator

# 1. 初始化生成器 (自动读取环境变量)
# 也可以手动传入 api_key 参数
generator = create_generator("tongyi") 

# 2. 生成图片
try:
    # 简单生成
    result = generator.generate("一只可爱的猫")
    
    # LiblibAI 需要指定 model_id
    # liblib_gen = create_generator("liblib")
    # result = liblib_gen.generate("A cute cat", model_id="liblib-sdxl-model")
    #
    # Codex 渠道返回 PNG bytes，可自行保存到文件
    # codex_gen = create_generator("codex")
    # result = codex_gen.generate("A cute cat astronaut")
    
    print(result)
except Exception as e:
    print(f"Error: {e}")

# 3. 获取模型列表 (如果支持)
models = generator.get_models()
for model in models:
    print(model)
```
