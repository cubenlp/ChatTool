# ChatTool PyPI CLI 设计

> 当前版本把 `chattool pypi` 收口为最小命令集：`init`、`build`、`check`、`upload`、`probe`。上传不再做额外封装，直接复用原始 `twine upload` 行为。

## 设计目标

- 只保留本地最常用的五个命令：模板初始化、构建、元数据检查、上传、仓库探测。
- 避免在 PyPI 上传上叠加额外策略、凭证管理和交互流程。
- 和标准 Python 打包工具保持一致，底层直接复用 `build` 与 `twine`。

## 非目标

- 不提供 `publish` / `release` 这类额外编排命令。
- 不接管 `twine` 的凭证发现、仓库选择和交互提示。
- 不自动改版本号、不自动打 tag、不自动推送 commit。

## 命令总览

```bash
chattool pypi init
chattool pypi build
chattool pypi check
chattool pypi upload
chattool pypi probe
```

## 行为边界

### `chattool pypi init`

- 生成最小可发布的 `src/` 布局 Python 包骨架。
- 不做交互补参；缺少 `NAME` 时可以从 `--project-dir` 目录名推断，否则直接报错。

### `chattool pypi build`

- 调用 `python -m build`。
- 默认清理旧的 `dist/` 产物。
- 默认同时构建 `sdist` 和 `wheel`。

### `chattool pypi check`

- 调用 `python -m twine check dist/*`。
- 若 `dist/` 为空，直接报错。

### `chattool pypi upload`

- 调用默认的 `python -m twine upload dist/*`。
- 只支持薄封装参数，例如 `--skip-existing`。
- 不再提供仓库、凭证、确认和交互机制；如需复杂上传参数，直接使用原始 `twine upload`。

### `chattool pypi probe`

- 检查候选包名和版本在目标仓库是否已被占用。
- 默认从当前项目的 `pyproject.toml` 读取名称和版本。

## 原则

- CLI 简单直接，缺参即失败，不进入向导。
- 上传行为尽量与用户手写 `twine upload` 保持一致。
- `chattool pypi` 负责模板和本地校验，不负责发版策略。
