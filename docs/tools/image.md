# AI 绘图工具开发者指南

ChatTool 已集成多个主流 AI 绘图工具的 API 调用，支持命令行 (CLI) 和 Python 代码两种调用方式。

## 支持平台

| 平台 | Provider ID | 环境变量 | 说明 |
| :--- | :--- | :--- | :--- |
| **通义万相** | `tongyi` | `DASHSCOPE_API_KEY` | [阿里云 DashScope](https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-wanxiang-api-details) |
| **Hugging Face** | `huggingface` | `HUGGINGFACE_HUB_TOKEN` | [Inference API](https://huggingface.co/docs/api-inference/detailed_parameters#text-to-image) |
| **LiblibAI** | `liblib` | `LIBLIB_ACCESS_KEY`, `LIBLIB_SECRET_KEY` | [Liblib API](https://liblibai.feishu.cn/wiki/UAMVw67NcifQHukf8fpccgS5n6d) |
| **Pollinations.ai** | `pollinations` | `POLLINATIONS_API_KEY`, `POLLINATIONS_MODEL_ID`(可选) | [Pollinations API](https://enter.pollinations.ai/api/docs) |
| **SiliconFlow** | `siliconflow` | `SILICONFLOW_API_KEY`, `SILICONFLOW_MODEL_ID` | [SiliconFlow API](https://docs.siliconflow.cn/) |

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

### SiliconFlow

```bash
# 生成图片
chattool image siliconflow generate "a cute dog"

# 指定模型和尺寸
chattool image siliconflow generate "a cute dog" --model "black-forest-labs/FLUX.1-schnell" --size "1024x1024"
```

### LiblibAI

使用 `chattool image generate` 命令：

```bash
# 语法
chattool image generate -p <provider> <prompt> [options]
```

**示例：**

```bash
# 通义万相
chattool image generate -p tongyi "一只在屋顶晒太阳的赛博朋克猫" -o cat_tongyi.png

# Hugging Face (默认使用 FLUX.1)
chattool image generate -p huggingface "A futuristic city at night, neon lights" -o city_hf.png

# LiblibAI (需指定 model-id)
chattool image generate -p liblib "A cute dog" --model-id liblib-sdxl-model -o dog_liblib.png
```

**参数说明：**

*   `-p, --provider`: 指定服务商 (`tongyi`, `huggingface`, `pollinations`, `siliconflow`, `liblib`)。
*   `-o, --output`: 输出文件路径。如果未指定，部分 Provider 可能会直接打印 URL。
*   `--model-id`: 指定使用的模型 ID（LiblibAI 必填，Hugging Face 可选）。

### 查看模型列表

使用 `chattool image list-models` 命令查看支持的模型（目前主要支持 LiblibAI）：

```bash
chattool image list-models -p liblib
```

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
    
    print(result)
except Exception as e:
    print(f"Error: {e}")

# 3. 获取模型列表 (如果支持)
models = generator.get_models()
for model in models:
    print(model)
```
