# test_chattool_image_interactive_basic

测试 `chattool image` 各类 `generate` 子命令在缺参时的默认交互补问行为。

## 用例 1：`huggingface generate` 缺少 prompt/output 时自动补问

预期过程和结果：
1. 在交互可用环境下执行 `chattool image huggingface generate`。
2. CLI 应补问 `prompt` 和 `output`，随后保存结果文件。

## 用例 2：另一类 `generate` 命令也应沿用相同机制

预期过程和结果：
1. `liblib` / `tongyi` / `pollinations` / `siliconflow` 的 `generate` 也都应使用同一套 prompt schema。
2. 这批命令的细节链路可在各自命令的专题测试中继续补充；这里主要覆盖共享交互机制的代表命令。

## 用例 3：`-I` 禁用交互时报错

预期过程和结果：
1. 执行 `chattool image huggingface generate -I`。
2. CLI 应直接报缺少必要参数。
