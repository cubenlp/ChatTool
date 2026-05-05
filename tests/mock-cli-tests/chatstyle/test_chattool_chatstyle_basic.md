# test_chattool_chatstyle_basic

## 目标

验证 ChatStyle 迁移后的兼容边界：

- 旧 `chattool.interaction` prompt / choice / render / constants 入口仍可导入。
- `CommandSchema` 仍保留在 `chattool.interaction.command_schema`。
- `add_interactive_option()` 与手写 interactive option 共享 `chattool.chatstyle.constants.INTERACTIVE_OPTION_HELP`。
- `chattool.utils.mask_secret()` 与 `chattool.chatstyle.mask.mask_secret()` 行为一致。

## 预期过程和结果

1. 导入 `chattool.chatstyle` 的 prompt、choice、mask 和 constants。
2. 导入旧 `chattool.interaction` 入口，确认函数对象来自新实现或行为一致。
3. 构造一个最小 Click 命令，使用 `add_interactive_option()`，确认 `--help` 中包含统一文案。
4. 调用 `mask_secret()`，确认旧 utils 入口和新 chatstyle 入口输出一致。

## 参考执行脚本

```sh
python -m pytest -q tests/mock-cli-tests/chatstyle/test_chattool_chatstyle_basic.py
```
