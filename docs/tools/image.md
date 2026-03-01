# AI 绘图工具开发者指南

ChatTool 已集成多个主流 AI 绘图工具的 API 调用，支持命令行 (CLI) 和 Python 代码两种调用方式。

## 支持平台

| 平台 | Provider ID | 环境变量 | 说明 |
| :--- | :--- | :--- | :--- |
| **通义万相** | `tongyi` | `DASHSCOPE_API_KEY` | [阿里云 DashScope](https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-wanxiang-api-details) |
| **Hugging Face** | `huggingface` | `HUGGINGFACE_HUB_TOKEN` | [Inference API](https://huggingface.co/docs/api-inference/detailed_parameters#text-to-image) |
| **LiblibAI** | `liblib` | `LIBLIB_ACCESS_KEY`, `LIBLIB_SECRET_KEY` | [Liblib API](https://liblibai.feishu.cn/wiki/UAMVw67NcifQHukf8fpccgS5n6d) |
| **Bing** | `bing` | `BING_COOKIE_U` | 基于逆向工程，非官方 API |

## 1. 配置环境变量

使用 `chatenv` 命令初始化配置：

```bash
# 查看支持的配置类型
chatenv init --help

# 交互式设置 Key
chatenv init -i -t tongyi -t hf -t liblib
```

或者直接编辑 `.env` 文件。

## 2. 命令行使用 (CLI)

### 生成图片

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

*   `-p, --provider`: 指定服务商 (`tongyi`, `huggingface`, `liblib`, `bing`)。
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
