# test_chattool_image_codex_basic

测试 `chattool image codex` 的基础编排，重点覆盖默认输出路径和参数透传。

## 用例 1：缺少 prompt 时自动补问，并写入统一默认输出路径

预期过程和结果：
1. 在交互可用环境下执行 `chattool image codex generate`。
2. CLI 应补问 `prompt`。
3. 若未传 `-o/--output`，应默认写入当前目录下 `generated/image_codex_<model>_<timestamp>.png`。

## 用例 2：显式选项应透传给 provider，并保存到指定输出路径

预期过程和结果：
1. 执行 `chattool image codex generate "a fox" --aspect-ratio portrait --image-model gpt-image-2-high --host-model gpt-5.4 --base-url <url> --timeout 12 -o <path>`。
2. CLI 应将这些临时选项传给 `create_generator("codex", ...)`；长期 token/base/model 默认值来自 OpenAI/OAI 配置，不再通过独立 Codex env 或 auth.json 路径管理。OpenAI/OAI 配置可同时保存 access token 日期元数据，provider 在配置日期过期时优先通过 refresh token 换取新的 access token。
3. provider 返回的 PNG bytes 应写入指定路径。

## 用例 3：provider 失败时 CLI 应以非 0 状态退出

预期过程和结果：
1. mock provider 在 `generate()` 中抛出异常。
2. 执行 `chattool image codex generate "a fox" -I`。
3. CLI 应输出 Click 风格错误信息，并返回非 0 exit code，避免脚本或 CI 将失败误判为成功。
