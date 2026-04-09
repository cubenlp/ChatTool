# test_chatpypi_shortcut_basic

测试 `chatpypi` 快捷入口的参数路由行为。

## 用例 1：`chatpypi <name>` 直接视为 `pypi init <name>`

预期过程和结果：
1. 执行 `chatpypi mypkg`。
2. 快捷入口应自动把它改写为 `chattool pypi init mypkg`，而不是把 `mypkg` 当成 `pypi` 子命令名。

## 用例 2：显式子命令仍保持原样透传

预期过程和结果：
1. 执行 `chatpypi build`。
2. 快捷入口应改写为 `chattool pypi build`。
