# test_chattool_image_basic

测试 `chattool image` 的基础链路，覆盖各图像后端的 generate/list-models 流程。

## 元信息

- 命令：`chattool image <provider> <command> [args]`
- 目的：验证图像生成 CLI 的基础能力。
- 标签：`cli`
- 前置条件：具备对应服务的 API 凭证。
- 环境准备：配置各 provider 的环境变量（如 `DASHSCOPE_API_KEY`、`HUGGINGFACE_HUB_TOKEN`、`LIBLIB_ACCESS_KEY`、`LIBLIB_SECRET_KEY`、`POLLINATIONS_API_KEY`、`SILICONFLOW_API_KEY`）。
- 回滚：删除生成的图片文件。

## 用例 1：tongyi 生成

- 初始环境准备：
  - 配置 `DASHSCOPE_API_KEY`。
- 相关文件：
  - `<tmp>/tongyi.png`

预期过程和结果：
  1. 执行 `chattool image tongyi generate "a cat" --output <path>`，预期输出图片 URL 并保存文件。

参考执行脚本（伪代码）：

```sh
chattool image tongyi generate "a cat" --output /tmp/tongyi.png
```

## 用例 2：huggingface 生成

- 初始环境准备：
  - 配置 `HUGGINGFACE_HUB_TOKEN`。
- 相关文件：
  - `<tmp>/hf.png`

预期过程和结果：
  1. 执行 `chattool image huggingface generate "a cat" --output <path>`，预期保存输出文件。

参考执行脚本（伪代码）：

```sh
chattool image huggingface generate "a cat" --output /tmp/hf.png
```

## 用例 3：liblib 生成与列出模型

- 初始环境准备：
  - 配置 `LIBLIB_ACCESS_KEY` 与 `LIBLIB_SECRET_KEY`。
- 相关文件：
  - `<tmp>/liblib.png`

预期过程和结果：
  1. 执行 `chattool image liblib list-models`，预期输出模型列表。
  2. 执行 `chattool image liblib generate "a cat" --model-id <id> --output <path>`，预期输出图片 URL 并保存文件。

参考执行脚本（伪代码）：

```sh
chattool image liblib list-models
chattool image liblib generate "a cat" --model-id xxx --output /tmp/liblib.png
```

## 用例 4：pollinations 生成与列出模型

- 初始环境准备：
  - 配置 `POLLINATIONS_API_KEY`（如需要）。
- 相关文件：
  - `<tmp>/pollinations.png`

预期过程和结果：
  1. 执行 `chattool image pollinations list-models`，预期输出模型列表。
  2. 执行 `chattool image pollinations generate "a cat" --model flux --output <path>`，预期输出图片 URL 并保存文件。

参考执行脚本（伪代码）：

```sh
chattool image pollinations list-models
chattool image pollinations generate "a cat" --model flux --output /tmp/pollinations.png
```

## 用例 5：siliconflow 生成与列出模型

- 初始环境准备：
  - 配置 `SILICONFLOW_API_KEY`（如需要）。
- 相关文件：
  - `<tmp>/siliconflow.png`

预期过程和结果：
  1. 执行 `chattool image siliconflow list-models`，预期输出模型列表。
  2. 执行 `chattool image siliconflow generate "a cat" --size 1024x1024 --output <path>`，预期输出图片 URL 并保存文件。

参考执行脚本（伪代码）：

```sh
chattool image siliconflow list-models
chattool image siliconflow generate "a cat" --size 1024x1024 --output /tmp/siliconflow.png
```

## 清理 / 回滚

- 删除输出图片文件。
