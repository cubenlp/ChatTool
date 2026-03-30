---
name: chattool-release
description: 处理 ChatTool 的发版准备与合并后发版执行。适用于版本号调整、CHANGELOG 收口、tag 时机判断、Publish Package 工作流检查、PyPI 校验，以及正式发版后补记 release.log。
version: 0.1.1
---

# ChatTool 发版

这个 skill 用于 ChatTool 的发版准备与正式发版动作。

边界：它从 `$chattool-dev-review` 结束的地方开始。普通功能开发验收继续用 `$chattool-dev-review`；涉及版本、tag、发布和发版记录时切到这个 skill。

## 适用场景

- 用户明确要求发版或切版本。
- 任务涉及 `src/chattool/__init__.py`、`CHANGELOG.md`、release tag、`Publish Package`。
- 需要判断“现在该不该打 tag”。
- 需要确认 PyPI 状态，或在正式发版后补写 `release.log`。

## 发版规则

1. tag 只能从已合并主线打
   - 不要从未合并的 PR 分支 head 打 tag。
   - 打 tag 前先把本地 `master` 快进到最新 `origin/master`。
   - 正式发版统一使用标准 tag 格式 `vX.Y.Z`，不要再打裸版本 `X.Y.Z`。
   - 如果 PR 还没合并，就停下来，明确说明“现在只到 release-ready，还不能正式发版”。

2. 先确认发版输入
   - 检查 `src/chattool/__init__.py` 中的版本号。
   - 检查 `CHANGELOG.md` 中对应版本条目。
   - 检查本地和远端是否已经存在同名 `vX.Y.Z` tag。
   - 如果是正式发布，再检查 PyPI 上是否已经有该版本。

3. 推 tag 前先验证发版路径
   - 跑最小相关测试。
   - 构建发行包并执行 `twine check`。
   - 如果这次发版改了兼容性声明，优先在最低支持 Python 上验证。

4. 推 tag 后再核发版结果
   - 从已合并的 `master` 创建 annotated `vX.Y.Z` tag。
   - 仅在验证通过后推送 tag。
   - 检查 `Publish Package` workflow，确认它会先剥离 tag 的 `v` 前缀再与 `__version__` 比对，并确认 PyPI 新版本已可见。

5. `release.log` 只能在正式发版完成后追加
   - 记录时间、版本、tag、commit、执行者和摘要。
   - 不要在 tag / publish 成功前提前写入。

## 执行流程

1. 先确认这次是“发版准备”还是“正式发版”。
2. 如果是正式发版：
   - 同步 `master`
   - 检查版本 / changelog / tag 唯一性
   - 跑验证
   - 创建并推送 tag
   - 检查 workflow 与 PyPI 结果
   - 追加 `release.log`
3. 如果只是准备：
   - 停在打 tag 之前
   - 明确告诉用户还差哪些 merge / release 动作

## 常用命令

```bash
git fetch origin
git checkout master
git pull --ff-only origin master
git tag --list 'v*'
git ls-remote --tags origin 'v*'
python -m build
python -m twine check dist/*
chattool gh pr-view --repo cubenlp/ChatTool --number <pr>
chattool gh pr-check --repo cubenlp/ChatTool --number <pr>
chattool gh run-view --repo cubenlp/ChatTool --run-id <id>
python - <<'PY'
import json, urllib.request
print(json.load(urllib.request.urlopen('https://pypi.org/pypi/chattool/json'))['info']['version'])
PY
```

## 输出要求

- 明确区分“已具备发版条件”和“已经正式发版”。
- 使用具体版本号、commit、tag、workflow id。
- 如果当前时机不该发版，要先指出，再停止危险动作。
