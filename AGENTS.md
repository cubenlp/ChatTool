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
- 新增 CLI 请同步更新 `docs/client.md` 和 README。
- 最小 import 原则：尽可能把 import 放到函数内，减少 CLI 启动时间。
