---
name: chattool-gh
description: 使用 `chattool gh` 完成 PR 创建、更新、查看与列表查询，并确保正文 Markdown 正确渲染。
version: 0.1.0
---

# ChatTool GitHub 帮助（中文）

目标：用 `chattool gh` 完成 PR 创建与更新，确保正文 Markdown 正确渲染。

## 前置

先初始化 GitHub 凭证（`chattool gh` 会自动读取）：
```
chattool env init -t gh
```

## 创建 PR（推荐）

使用 `--body-file` 防止换行被转义：
```
cat > /tmp/pr_body.md <<'EOF'
## Summary
- point 1
- point 2

## Notes
- note 1
EOF

chattool gh pr-create \
  --repo owner/repo \
  --base master \
  --head your-branch \
  --title "feat: add xyz" \
  --body-file /tmp/pr_body.md
```

## 更新 PR

```
chattool gh pr-update \
  --repo owner/repo \
  --number 123 \
  --body-file /tmp/pr_body.md
```

## 查看 / 列表

```
chattool gh pr-list --repo owner/repo
chattool gh pr-view --repo owner/repo --number 123
```

## 规范

- 始终用 `--body-file`，避免 `\n` 字符串导致的乱码。
- 保持 PR 文本结构化（Summary、Notes）。
