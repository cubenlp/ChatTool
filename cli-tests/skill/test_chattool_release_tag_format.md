# test_chattool_release_tag_format

校对 ChatTool 正式发版已统一使用 `vX.Y.Z` tag，且 `Publish Package` workflow 会在比对包版本时剥离 `v` 前缀。

## 元信息

- 命令：无
- 目的：避免 skill 与 GitHub Actions 的发版规则不一致，导致 post-merge 推送 `v6.4.1` 这类标准 tag 时 workflow 不发布。
- 标签：`doc-audit`, `skill`, `release`
- 前置条件：仓库内 release skill 和 `.github/workflows/publish.yml` 已更新。
- 环境准备：
  - 无
- 回滚：无

## 用例 1：校对标准 release tag 格式与 workflow 行为

- 初始环境准备：
  - 打开 `skills/chattool-release/SKILL.md`
  - 打开 `skills/chattool-release/SKILL.zh.md`
  - 打开 `.github/workflows/publish.yml`
- 相关文件：
  - `skills/chattool-release/SKILL.md`
  - `skills/chattool-release/SKILL.zh.md`
  - `.github/workflows/publish.yml`

预期过程和结果：
  1. `chattool-release` 中英文 skill 都明确要求正式发版使用 `vX.Y.Z` tag，而不是裸版本 tag。
  2. `Publish Package` workflow 只匹配 `v*` tag。
  3. workflow 在校验版本时会将 `GITHUB_REF_NAME` 的前导 `v` 去掉，再与 `src/chattool/__init__.py` 中的 `__version__` 比对。

参考执行脚本（伪代码）：

```sh
sed -n '1,220p' skills/chattool-release/SKILL.md
sed -n '1,220p' skills/chattool-release/SKILL.zh.md
sed -n '1,220p' .github/workflows/publish.yml
```
