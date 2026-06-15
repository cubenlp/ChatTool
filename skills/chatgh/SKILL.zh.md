---
name: chatgh
description: 使用独立 ChatGH CLI（`chatgh`）创建和更新 PR、检查 CI、查看 workflow run，并通过 chatenv 配置 GitHub 凭证。
version: 0.5.0
---

# ChatGH GitHub Helpers

使用 `chatgh` 处理 GitHub PR、CI 检查和 PR body 格式。不要再使用已移除的 `chattool gh` 入口。

## 凭证

把 GitHub token 保存到 typed env：

```bash
chatenv init -t gh
chatenv cat -t gh
```

推荐 key：`GITHUB_ACCESS_TOKEN`。

如需配置当前仓库的 Git HTTPS 凭证，使用：

```bash
chatgh set-token
```

## 创建 PR

优先使用 body 文件，避免 Markdown 换行转义问题：

```bash
cat > /tmp/pr_body.md <<'EOF'
## Summary
- point 1
- point 2

## Testing
- command 1
- command 2
EOF

chatgh pr-legacy create --repo owner/repo --base master --head your-branch --title "feat: add xyz" --body-file /tmp/pr_body.md
```

## 更新 PR

范围变化时同步更新 PR body：

```bash
chatgh pr-legacy edit --repo owner/repo --number 123 --body-file /tmp/pr_body.md
```

也可以更新 title、state 或 base branch：

```bash
chatgh pr-legacy edit --repo owner/repo --number 123 --title "feat: refine xyz" --state open
```

## 查看 PR 和 CI

能使用 generated 默认 `pr` 命令时优先使用：

```bash
chatgh pr list --repo owner/repo
chatgh pr view 123 --repo owner/repo
chatgh pr checks 123 --repo owner/repo
```

尚未迁移到 generated layer 的完整手写能力继续使用 `pr-legacy`：

```bash
chatgh pr-legacy checks --repo owner/repo --number 123 --wait
chatgh pr-legacy checks --repo owner/repo --number 123 --wait --interval 10 --timeout 600
chatgh run view --repo owner/repo --run-id 23494900414
chatgh run logs --repo owner/repo --job-id 68373094563
```

PR 更新后优先使用：

```bash
chatgh pr-legacy checks --repo owner/repo --number 123 --wait
```

只有明确需要快照时才使用不带 `--wait` 的 `pr checks`。

机器可读输出：

```bash
chatgh pr checks 123 --repo owner/repo --json-output
```

## 评论与合并

```bash
chatgh pr-legacy comment --repo owner/repo --number 123 --body "Looks good"
chatgh pr-legacy merge --repo owner/repo --number 123 --method squash
chatgh pr-legacy merge --repo owner/repo --number 123 --method squash --check
```

## 说明

- 创建或编辑 PR 时优先使用 `--body-file`。
- PR body 保持简短，并包含 `Summary` 与 `Testing`。
- 先用 `pr checks` 看整体状态，再查看具体 workflow run。
- CI 失败时用 `run view` 和 `run logs` 深挖，不要只凭 Web UI 猜测。
- 请求 review 前先从目标主分支更新并解决冲突。
