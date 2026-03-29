# uv 教程：安装、常用命令、项目结构与关键文件

这一篇单独讲 `uv`。

如果你现在的 Python 仓库还是以 `pip`、`venv`、`pip-tools`、`twine` 这类分散工具为主，那理解 `uv` 最重要的一点不是“它更快”，而是它把 **Python 版本管理**、**项目依赖管理**、**命令执行**、**工具安装** 和 **打包发布** 收到了一套 CLI 里。

本文基于 **2026-03-29** 查阅 Astral 官方 `uv` 文档整理，重点讲：

- `uv` 平时到底怎么用
- 常见命令应该按什么场景记
- 一个 `uv` 项目会多出哪些文件
- 如果你做的是 Python 包仓库，应该选哪种初始化方式

---

## 先把 `uv` 的定位说清楚

官方对 `uv` 的定位很明确：它既是 Python 包管理器，也是项目管理器，同时还覆盖了 Python 安装、工具安装和一套兼容 `pip` 的低层接口。

对日常开发来说，可以把它理解成 5 组能力：

- `uv python`：安装和切换 Python 版本
- `uv init / add / lock / sync / run`：管理项目
- `uvx` / `uv tool`：运行和安装命令行工具
- `uv build / publish`：构建和发布包
- `uv pip ...`：在保留旧工作流时替代 `pip`

如果你只记一句话，可以记这个：

> `uv` 不是“更快的 pip”而已，它更像是把 Python 项目开发链路收成一个统一入口。

---

## 第一步：安装 `uv`

官方推荐安装方式是独立安装脚本。

### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows PowerShell

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

如果你只是临时试用，也可以用 `pip`、Homebrew 等其他方式安装；但如果你准备把仓库迁到 `uv`，优先用官方安装方式更稳。

安装完先看版本：

```bash
uv self version
uv --version
uv -V
```

再看帮助：

```bash
uv --help
uv help
uv help init
```

---

## 第二步：先按场景记命令

`uv` 的命令很多，但大部分日常工作都能落在下面这几组。

### 1. 管 Python 版本

```bash
uv python install
uv python install 3.12
uv python install 3.11 3.12
uv python list
uv python pin 3.12
```

你可以这样理解：

- `uv python install`：装 Python
- `uv python list`：看本机和可用版本
- `uv python pin`：给当前项目写 `.python-version`

有一点和传统做法很不一样：

- `uv` 默认会按需自动下载缺失的 Python
- 所以很多时候你不用先手动装解释器，再建环境

---

### 2. 新建和维护项目

这是最常用的一组：

```bash
uv init
uv init myproj
uv init --package myproj
uv init --lib mylib

uv add requests
uv add 'httpx>=0.28'
uv add -r requirements.txt

uv remove requests

uv lock
uv lock --upgrade-package requests

uv sync

uv run python -V
uv run pytest -q
uv run ruff check
```

可以按这个心智模型记：

- `uv init`：初始化项目
- `uv add`：写依赖到 `pyproject.toml`，同时更新锁文件和环境
- `uv remove`：删依赖
- `uv lock`：更新 `uv.lock`
- `uv sync`：把环境同步到锁文件
- `uv run`：在项目环境里跑命令

`uv` 的项目流和手工 `pip install -r requirements.txt` 最大的区别是：

- 依赖声明放在 `pyproject.toml`
- 精确解析结果放在 `uv.lock`
- `uv run` 会在执行前检查锁文件和环境是否需要同步

也就是说，`uv` 更强调“项目状态一致”，而不是“你自己记得什么时候重装环境”。

---

### 3. 跑工具，不想全局污染环境

```bash
uvx ruff check
uvx pycowsay "hello"

uv tool install ruff
uv tool list
uv tool uninstall ruff
```

这里分两类：

- `uvx` / `uv tool run`：一次性临时运行
- `uv tool install`：长期安装到用户级工具目录

如果你之前用 `pipx` 装 `ruff`、`black`、`mkdocs`，这一层通常可以直接换成 `uv tool`。

---

### 4. 兼容旧的 `pip` 工作流

如果仓库一开始不想整体改成 `uv project` 模式，可以先从 `uv pip` 开始：

```bash
uv venv
uv pip install -r requirements.txt
uv pip list
uv pip tree
uv pip compile requirements.in -o requirements.txt
uv pip sync requirements.txt
```

这条路线适合：

- 先保留旧仓库布局
- 先把速度和环境创建切到 `uv`
- 后面再逐步迁到 `pyproject.toml + uv.lock`

如果你面对的是一个老项目，这通常是最稳的过渡方案。

---

### 5. 构建和发布包

```bash
uv build
uv publish
```

如果项目已经是可打包的 Python package，`uv` 也可以直接负责构建和发布，不一定要继续拆成 `python -m build` 和 `twine upload` 两段。

---

## 新项目应该怎么初始化

这是最容易一开始就选错的地方。

`uv init` 有几种常见模式。

### 普通应用项目

```bash
uv init myapp
```

默认生成的是应用模板，适合：

- 小脚本
- 服务端入口
- 个人命令行项目

结构大致是：

```text
myapp/
├── .python-version
├── README.md
├── main.py
└── pyproject.toml
```

---

### 可打包应用

```bash
uv init --package myapp
```

这时 `uv` 会用 `src/` 布局，并生成可安装项目，适合：

- 要发布到 PyPI 的 CLI
- 要单独写 tests 的项目
- 想让本地运行和安装后运行保持一致的应用

结构大致是：

```text
myapp/
├── .python-version
├── README.md
├── pyproject.toml
└── src/
    └── myapp/
        └── __init__.py
```

同时 `pyproject.toml` 里会包含：

- `[project]`
- `[project.scripts]`
- `[build-system]`

---

### 库项目

```bash
uv init --lib mylib
```

如果你做的是 Python library，这通常才是最适合的入口。

官方说明里，`--lib` 会隐含 `--package`，因此它天然就是可构建、可发布、`src/` 布局的项目。

结构大致是：

```text
mylib/
├── .python-version
├── README.md
├── pyproject.toml
└── src/
    └── mylib/
        ├── __init__.py
        └── py.typed
```

这类结构特别适合像 ChatTool 这种仓库，因为它本来就有：

- 包发布需求
- `src/` 布局
- CLI 入口
- 文档和测试分层

---

### 只想先落一个最小 `pyproject.toml`

```bash
uv init --bare myproj
```

这会只生成最小项目骨架，适合：

- 你已经有仓库目录
- 你只想先切换项目元数据管理
- 你准备手工组织源码结构

---

## 一个 `uv` 项目里最重要的几个文件

如果你要把仓库改成 `uv`，最先要认识的不是命令，而是文件职责。

### `pyproject.toml`

这是项目的中心文件。

主要承载：

- 项目元数据
- Python 版本要求，例如 `requires-python`
- 依赖声明
- 构建系统
- `[project.scripts]` 之类的入口点
- `[tool.uv]` 下的 `uv` 配置

简单说：

- “我想要什么”写在 `pyproject.toml`

---

### `uv.lock`

这是 `uv` 的锁文件，保存精确解析后的依赖版本。

主要特点：

- 跨平台
- 应该提交到版本控制
- 不建议手工编辑

简单说：

- “最终解析成什么版本”写在 `uv.lock`

---

### `.python-version`

这个文件指定项目默认使用的 Python 版本。

常见生成方式：

```bash
uv python pin 3.12
```

简单说：

- “这个仓库默认用哪版 Python”写在 `.python-version`

---

### `.venv`

这是项目虚拟环境目录。

常见触发方式：

- 第一次 `uv run`
- 第一次 `uv sync`
- 第一次 `uv lock`
- 手工 `uv venv`

一般建议：

- 放进 `.gitignore`
- 让 `uv` 管，不要手工往里塞东西

---

## 如果你要从 pip 仓库迁到 uv，建议这样走

对一个已经存在的 Python 仓库，更稳的顺序通常不是“一步到位重写”，而是分层替换。

### 路线 A：先保留旧工作流，只把底层工具换成 `uv`

```bash
uv venv
uv pip install -r requirements.txt
uv pip compile requirements.in -o requirements.txt
uv pip sync requirements.txt
```

适合：

- 老仓库
- CI 还大量依赖 `requirements.txt`
- 团队还没准备好一次性切换到 `pyproject.toml`

---

### 路线 B：直接切到 `uv project` 模式

如果仓库本来就已经有 `pyproject.toml`，或者你准备把它作为统一入口，更适合直接切到：

```bash
uv add ...
uv lock
uv sync
uv run ...
```

这个阶段通常要一起确认：

- 是否保留当前 build backend
- 是否引入 `uv.lock`
- 是否写入 `.python-version`
- CI 里是改成 `uv sync` 还是暂时保留旧流程

---

## 对 Python 包仓库，最值得优先记住的命令

如果你平时维护的是类似 ChatTool 这种仓库，我建议先把下面这组记熟：

```bash
uv python pin 3.12
uv add requests
uv remove requests
uv lock
uv sync
uv run pytest -q
uv run python -m chattool
uv build
uv publish
```

再加一组“兼容旧仓库”的过渡命令：

```bash
uv venv
uv pip install -r requirements.txt
uv pip sync requirements.txt
```

这两组基本就覆盖了：

- 新项目
- 包项目
- 旧仓库迁移
- CI 过渡

---

## 最后用一句话收尾

如果你要把一个 Python 仓库迁到 `uv`，真正需要先统一的不是命令细节，而是团队约定：

- 用 `uv pip` 先过渡，还是直接切 `uv project`
- `pyproject.toml` 是不是唯一依赖真相
- `uv.lock` 要不要进仓库
- `.python-version` 要不要跟着一起管

这些边界一旦定下来，剩下的 CLI 操作反而很顺。

## 参考链接

- 官方首页：<https://docs.astral.sh/uv/>
- 项目指南：<https://docs.astral.sh/uv/guides/projects/>
- 项目创建：<https://docs.astral.sh/uv/concepts/projects/init/>
- Python 安装：<https://docs.astral.sh/uv/guides/install-python/>
- 功能总览：<https://docs.astral.sh/uv/getting-started/features/>
- 帮助与版本：<https://docs.astral.sh/uv/getting-started/help/>
