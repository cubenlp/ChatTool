# 飞书 Skill：docx 采用说明

这份文档记录扩 `chattool lark doc ...` 时应遵守的采用策略。

## 默认策略

- 优先把高频、稳定、可复用的文档操作做成 CLI
- 先写 `cli-tests/lark/*.md`，再补实现
- 结构化能力只在 block API 明确可行时进入主线

## 可以吸收进 CLI 的内容

- Markdown 到 docx block 的稳定映射
- block JSON 的安全追加策略
- 文档链接获取与通知工作流

## 不直接照搬进主线的内容

- 大量一次性脚本
- 与当前 CLI 结构不一致的实验性命令面
- 没有真实测试路径的临时封装
