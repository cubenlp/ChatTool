---
name: chattool-gh
description: 使用 `chattool gh` 完成 PR 创建、更新、查看、CI 状态检查与维护，并确保正文 Markdown 正确渲染。
version: 0.3.0
---

# ChatTool GitHub 帮助（中文）

目标：用 `chattool gh` 完成 PR 创建、更新、CI 排查与后续维护，确保正文 Markdown 正确渲染。

## 前置

先初始化 GitHub 凭证（`chattool gh` 会自动读取）：
```
chatenv init -t gh
chatenv cat -t gh
```

常用配置项：
- `GITHUB_ACCESS_TOKEN`
- `GITHUB_DEFAULT_REPO`

## 创建 PR（推荐）

使用 `--body-file` 防止换行被转义：
```
cat > /tmp/pr_body.md <<'EOF'
## Summary
- point 1
- point 2

## Testing
- command 1
- command 2
EOF

chattool gh pr-create \
  --repo owner/repo \
  --base master \
  --head your-branch \
  --title "feat: add xyz" \
  --body-file /tmp/pr_body.md
```

## 更新 PR

当范围变化时，及时同步 PR 正文：
```
chattool gh pr-update \
  --repo owner/repo \
  --number 123 \
  --body-file /tmp/pr_body.md
```

也可以顺手改标题、状态或基线分支：

```
chattool gh pr-update \
  --repo owner/repo \
  --number 123 \
  --title "feat: refine xyz" \
  --state open
```

## 查看 / 列表 / 检查

```
chattool gh pr-list --repo owner/repo
chattool gh pr-view --repo owner/repo --number 123
chattool gh pr-check --repo owner/repo --number 123
chattool gh pr-check --repo owner/repo --number 123 --wait
chattool gh pr-check --repo owner/repo --number 123 --wait --interval 10 --timeout 600
chattool gh run-view --repo owner/repo --run-id 23494900414
chattool gh job-logs --repo owner/repo --job-id 68373094563
```

`pr-check` 适合在 push 之后或 CI 异常时使用，会汇总：
- combined status
- check runs
- workflow runs

如果带上 `--wait`，会持续轮询直到 checks 和 workflow runs 都结束：
- 默认不设超时，会一直等到完成
- `--interval <seconds>` 控制轮询间隔
- 只有显式传 `--timeout <seconds>` 时，才会在超时后报错

需要机器可读结果时：

```
chattool gh pr-check --repo owner/repo --number 123 --json-output
```

## 评论 / 合并

```
chattool gh pr-comment --repo owner/repo --number 123 --body "Looks good"
chattool gh pr-merge --repo owner/repo --number 123 --method squash --confirm
chattool gh pr-merge --repo owner/repo --number 123 --method squash --confirm --check
```

## 规范

- 始终用 `--body-file`，避免 `\n` 字符串导致的乱码。
- 保持 PR 文本结构化（`Summary`、`Testing`）。
- 需要看 PR 的 CI 状态时，优先用 `pr-check`，不要手工来回翻 GitHub Actions 页面。
- 提交评审 / MR 前，先从目标主分支更新并处理冲突，不要把可避免的合并债务留给评审阶段。
- 如果 CI 已经报红，先用 `pr-check` 定位，再用 `run-view` / `job-logs` 下钻，不要在网页上盲猜。
- 扩展 `chattool gh` 时，优先参考 `docs/client.md` 里列出的 GitHub REST API 与 PyGithub 文档。
