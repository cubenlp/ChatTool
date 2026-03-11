# ChatTool Agent Notes

## 项目信息
- 主语言：Python
- CLI 入口：`chattool`、`chatenv`、`chatskill`
- 代码路径：`src/chattool/`
- Skills 目录：`skills/`

## 常用命令
- 运行测试：`python -m pytest -q`
- 生成包：`python -m build`

## 注意事项
- 仓库包含 `src-old/`，pytest 可能因模块同名冲突导致收集失败。
- 新增 CLI 请同步更新 `docs/client.md` 和 README。
