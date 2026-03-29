# uv 配置

使用 `chattool setup uv` 可以把当前 Python 项目初始化到 `uv` 工作流。

它会按顺序做这些事：

1. 如有需要先安装 `uv`
2. 在项目目录执行 `uv python pin`
3. 生成或更新 `uv.lock`
4. 执行 `uv sync`
5. 如果项目存在 `dev` extra，则默认执行 `uv sync --extra dev`
6. 可选把当前项目 `.venv/bin/activate` 追加到 `~/.zshrc` / `~/.bashrc`

## 最简用法

在当前项目目录执行：

```bash
chattool setup uv
```

## 指定项目目录和 Python 版本

```bash
chattool setup uv --project-dir ~/workspace/ChatTool --python 3.12
```

如果项目已经有 `.python-version`，默认会优先复用；否则会尝试从 `pyproject.toml` 的 Python classifiers 推断版本。

## 配置镜像

如果你希望顺手写入 `uv` 默认镜像：

```bash
chattool setup uv --default-index https://pypi.tuna.tsinghua.edu.cn/simple/
```

这会把默认索引写入：

```text
~/.config/uv/uv.toml
```

## 追加 shell 激活脚本

如果你想保留“进入终端后直接 `chattool ...` / `pytest ...`”的手感，可以把当前项目的 `.venv` 激活脚本追加到 shell rc：

```bash
chattool setup uv --activate-shell
```

命令会向当前 shell 对应的 rc 文件写入一段受管区块：

- `~/.zshrc`
- `~/.bashrc`

执行完成后重新加载即可：

```bash
source ~/.zshrc
```

或：

```bash
source ~/.bashrc
```

## 开发态项目的推荐用法

对像 ChatTool 这种长期开发中的仓库，比较自然的路径是：

```bash
cd /path/to/project
chattool setup uv --activate-shell
```

之后日常开发通常就是：

```bash
source .venv/bin/activate
chattool ...
pytest -q
```

如果只是改源码，通常不需要重新初始化；只有依赖变化、切换依赖分支、或删掉 `.venv` 后，才需要重新同步。
