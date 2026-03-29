# uv 教程：从 conda 心智切到 Python 原生工作流

这一篇不是命令手册，而是一次“脑回路切换”。

如果你之前更多使用 `conda`，第一次接触 `uv` 很容易产生几个疑问：

- `uv` 到底是“更快的 pip”，还是“新的 conda”？
- 它是不是只能在项目里用？
- 没有项目时，我装 CLI 工具该怎么办？
- 多个项目都要 Python，不会互相冲突吗？

这几个问题背后，其实是同一个核心点：

> `uv` 的中心单位通常是“Python 项目”和“Python 工具”，而不是 `conda` 风格的“一个大而全的命名环境”。

本文结合从 `conda` 心智迁移时最容易卡住的地方整理。重点不是“列命令”，而是解释：

- `uv` 的定位和设计理念
- Python 解释器、环境、项目、工具这四层应该怎么分
- 项目外怎么用 `uv`
- 多项目之间如何共存
- 什么时候该用 `uv`，什么时候 `conda` 依然更合适

---

## 先给结论：`uv` 不等于 “新的 conda”

如果只用一句话来概括：

- `uv` 更像是 **Python 官方生态的统一工作台**
- `conda` 更像是 **完整运行环境的打包和分发系统**

`uv` 站在这些 Python 原生约定上工作：

- `pyproject.toml`
- `venv`
- PyPI
- `pip` 风格依赖规范
- 项目内 `.venv`

它想解决的是：

- 安装 Python
- 创建和同步虚拟环境
- 管理项目依赖
- 运行脚本和命令
- 安装 CLI 工具

它不试图把“整个软件世界”都纳进来。相比之下，`conda` 不只是管 Python 包，还能管理：

- Python 解释器
- Python 包
- C/C++ 二进制依赖
- CUDA、MKL、BLAS 等科学计算栈
- R 及其他语言组件

所以两者的差异，不是命令风格不同，而是“它们眼里的世界”不同。

---

## 先分清四层：解释器、环境、项目、工具

理解 `uv`，最重要的是不要把所有东西都叫“环境”。

### 1. Python 解释器

这是最底层的“Python 本体”。

```bash
uv python install 3.12
uv python list
```

这一层只解决一件事：

- 你的机器上有哪些 Python 版本可以用

它还没有回答“这个 Python 装了哪些第三方包”。

---

### 2. 环境

环境的作用是：

- 决定某次运行能看到哪些依赖

在 `uv` 里，环境通常是虚拟环境，也就是 `venv`。最常见的就是项目目录里的 `.venv`，也可以是你自己放在别处的长期环境。

```bash
uv venv
uv venv ~/.venvs/default --python 3.12
```

这里最关键的一句话是：

> Python 解释器和 Python 环境是两回事。

同一个 Python 3.12，可以对应很多个环境。

---

### 3. 项目

项目层是 `uv` 最擅长、也最推荐的工作方式。

一个典型 `uv` 项目通常包含：

- `pyproject.toml`
- `uv.lock`
- `.python-version`
- `.venv`

这些文件分别解决不同问题：

- `pyproject.toml`：项目声明和依赖声明
- `uv.lock`：精确锁定后的依赖结果
- `.python-version`：这个项目默认用哪一个 Python
- `.venv`：项目实际运行的环境

这一层的关键不是“装包”，而是：

- 让项目依赖可声明
- 让团队环境可复现
- 让运行命令和项目状态保持一致

---

### 4. 工具

这层是很多 `conda` 用户刚接触 `uv` 时最容易忽略的。

你并不总是在开发项目。有时候你只是想要一个命令：

- `ruff`
- `black`
- `httpie`
- `yt-dlp`
- `chattool`

这时候你要的不是项目环境，而是“工具环境”。

`uv` 专门为这个场景提供了：

- `uvx`：临时运行工具
- `uv tool install`：长期安装工具

```bash
uvx ruff check .
uv tool install ruff
uv tool install 'chattool[dev]'
```

所以 `uv` 不是“只能和项目绑定”。更准确地说：

> `uv` 是项目优先，但不是项目专属。

---

## 用一张图建立直觉

如果把 `uv` 的世界画成一棵树，它更像这样：

```text
Python 3.12 interpreter
├── /Users/you/work/api/.venv
├── /Users/you/work/bot/.venv
├── /Users/you/.venvs/default
└── uv tool envs
    ├── ruff
    ├── black
    └── chattool
```

这里有三个容易一下想通的点：

- 多个项目可以共用同一个 Python 解释器
- 每个项目可以有自己独立的依赖环境
- CLI 工具也可以放在自己的隔离环境里，而不是污染某个项目

所以不是“多个项目的 Python 不能共存”，而是：

- **解释器可以共享**
- **环境彼此隔离**
- **工具单独托管**

这正是 `uv` 想要的状态。

---

## `uv` 和 `conda` 的差别，最好从“默认工作方式”理解

| 问题 | `conda` 常见思路 | `uv` 常见思路 |
|------|------------------|---------------|
| 中心单位是什么 | 一个命名环境 | 一个项目，或一个工具 |
| 依赖来源 | conda channels | PyPI |
| 默认环境组织方式 | `base` + 多个环境名 | 项目内 `.venv` + tools |
| 擅长什么 | 完整运行环境、科学计算栈 | Python 项目开发、脚本、CLI 工具 |
| 二进制系统依赖 | 强 | 相对弱，主要围绕 Python 包 |
| 心智模型 | “建一个环境箱子” | “解释器、项目、工具分层管理” |

如果你过去是这样用 `conda` 的：

```bash
conda create -n dev python=3.12
conda activate dev
conda install requests
```

那么在 `uv` 里，最接近的对应关系是：

```bash
uv venv ~/.venvs/dev --python 3.12
source ~/.venvs/dev/bin/activate
uv pip install requests
```

这说明 `uv` 不是不能做“项目外环境”，只是它默认更鼓励你把环境放回具体项目里。

---

## 为什么很多人会误以为 “`uv` 只能在项目里用”

因为 `uv` 对正式开发的最佳实践非常明确：

- 每个项目一个 `.venv`
- 依赖写进 `pyproject.toml`
- 锁定结果写进 `uv.lock`
- 用 `uv run` 执行项目命令

这套流程非常顺，所以你会感觉它“天然和项目绑定”。

这种感觉并不算错，但它不是完整答案。更完整的答案是：

- **项目开发**：优先用项目内 `.venv`
- **项目外 CLI 工具**：优先用 `uv tool install` 或 `uvx`
- **项目外长期个人环境**：自己建 `~/.venvs/...`
- **一次性脚本**：直接用 `uv run`

也就是说，`uv` 的思路不是“必须有项目”，而是“不同场景用不同层”。

---

## 四个最常见场景，分别应该怎么用

下面这部分最实用。把命令记成“场景”，比背子命令快得多。

### 场景 1：我在做一个正式 Python 项目

这是 `uv` 最舒服的场景。

```bash
uv init myapp
cd myapp
uv python pin 3.12
uv add requests
uv run python main.py
```

如果你继续开发这个项目，常用命令通常就是这组：

```bash
uv add httpx
uv remove requests
uv lock
uv sync
uv run pytest -q
uv run ruff check
```

这个模式下，最重要的不是“环境在哪”，而是：

- 项目依赖在 `pyproject.toml`
- 环境由 `uv` 自动维护
- 运行命令通过 `uv run` 对齐当前项目状态

---

### 场景 2：我没有项目，只是想装 CLI 工具

这是很多人误以为 `uv` 不好用的地方，但实际上它支持得很好。

如果只是临时跑一次：

```bash
uvx ruff check .
uvx black --version
```

如果你想把命令长期装在机器上：

```bash
uv tool install ruff
uv tool install black
uv tool install httpie
```

如果工具命令没有立刻进入 `PATH`，可以执行：

```bash
uv tool update-shell
```

这个场景里，`uv` 更像是 `pipx` 的统一升级版，而不是 `conda env` 的替代品。

---

### 场景 3：我没有项目，但想维护一个长期个人环境

如果你就是习惯有一个“自己的默认 Python 环境”，`uv` 也能做。

```bash
uv python install 3.12
uv venv ~/.venvs/default --python 3.12
source ~/.venvs/default/bin/activate
uv pip install ipython requests pandas
```

以后你只要激活这个环境，就可以把它当作“个人常用 Python 工作区”。

这不是 `uv` 最推荐的主路线，但完全可行，而且对从 `conda` 迁移过来的人很友好。

---

### 场景 4：我只是想在项目外跑一个脚本

如果脚本本身不复杂，甚至不需要先建项目。

```bash
uv run script.py
uv run python script.py
uv run --with requests script.py
```

这里的重点是：

- 你可以离开项目使用 Python
- 你也可以临时为脚本补一个依赖
- 不需要先手工造一个长期环境

如果你经常写小脚本，这条路线会比“先建环境，再装包，再清理”轻很多。

---

## 场景 5：我想把一个现有项目改造成 `uv`，到底是在改什么

这是从旧工作流迁到 `uv` 时最值得先想清楚的问题。

很多人会以为“改成 `uv`”就是把：

```bash
pip install ...
```

改成：

```bash
uv pip install ...
```

这当然算最表层的一步，但真正的迁移通常不只这一层。

如果用一句话概括，**把项目改造成 `uv`，本质上是在把“环境管理、依赖声明、命令执行”收回到项目自己身上。**

通常会涉及这几件事：

1. 确认项目已经有 `pyproject.toml` 作为中心配置。
2. 用 `uv` 来确定项目使用的 Python 版本，比如写入 `.python-version`。
3. 生成并提交 `uv.lock`，把可复现依赖固定下来。
4. 让团队默认用 `uv sync` / `uv run`，而不是各自手工 `pip install`。
5. 把“开发依赖”“可选能力”“命令入口”这些内容统一放回项目声明里。

换句话说，迁移重点不是“换一个更快的安装命令”，而是把项目状态变成：

- 可以声明
- 可以锁定
- 可以同步
- 可以复现

---

### 如果拿当前这类仓库来理解，迁移前后有什么区别

以 ChatTool 这种仓库为例，它已经有 `pyproject.toml`，也已经定义了不少 extras，例如：

- `dev`
- `docs`
- `tests`
- `tools`

这说明它离 `uv` 项目工作流其实已经不远了。真正缺的通常是：

- `.python-version`
- `uv.lock`
- 一套明确的 `uv` 日常命令约定

所以对这种仓库来说，“改造成 `uv`”通常不是重构目录结构，而更像是：

- 把团队入口从 `pip install -e .[dev]` 迁到 `uv sync --extra dev`
- 把运行入口从裸 `python` / 裸 `pytest` 迁到 `uv run ...`
- 把“谁装了什么依赖”改成由 `uv.lock` 统一约束

---

## 场景 6：改造成 `uv` 之后，我每天怎么工作

这一段最适合当成你的日常模板。

### 第一次拿到项目

如果你是第一次 clone 仓库，常见流程是：

```bash
cd project
uv python install 3.12
uv sync --extra dev
```

做完之后，项目的 `.venv` 就准备好了。

接下来运行命令，推荐直接：

```bash
uv run pytest -q
uv run ruff check
uv run python -m yourpkg
```

如果你更喜欢传统 shell 习惯，也可以：

```bash
uv sync --extra dev
source .venv/bin/activate
pytest -q
python -m yourpkg
```

但在 `uv` 世界里，默认更推荐 `uv run`，因为它会先帮你确认环境是不是最新。

---

### 平时只是改代码

如果你只是修改：

- `.py` 源码
- 测试
- 文档

通常**不需要重新初始化环境**。

直接继续跑：

```bash
uv run pytest -q
uv run python -m yourpkg
```

这是因为 `uv sync` 默认会把项目以 editable 方式装进环境里。也就是说，源码改动会直接反映到运行结果，不需要每改一次代码都重装一次项目。[uv 锁定与同步文档](https://docs.astral.sh/uv/concepts/projects/sync/)

---

### 什么时候需要重新 `sync`

这些场景通常值得重新执行一次：

- 你修改了 `pyproject.toml`
- 你新增或删除了依赖
- 你切换了分支，而分支里的依赖定义不同
- 团队里有人更新了 `uv.lock`
- 你本地 `.venv` 被删了

这时候执行：

```bash
uv sync
```

如果项目用到了 extras，就按需要带上：

```bash
uv sync --extra dev
uv sync --extra docs
uv sync --all-extras
```

---

### 什么时候甚至不用手工 `sync`

如果你日常都用：

```bash
uv run ...
```

那很多时候你甚至不用显式执行 `uv sync`。

因为 `uv run` 在运行前会先检查：

- `uv.lock` 是否和 `pyproject.toml` 一致
- 当前环境是否和锁文件一致

需要的话，它会自动更新锁文件并同步环境，然后再执行命令。[Working on projects](https://docs.astral.sh/uv/guides/projects/) [Locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)

所以对大多数日常开发来说，真实体验更接近：

- 进入项目目录
- 直接 `uv run pytest -q`
- 直接 `uv run python -m yourpkg`

而不是“每次开终端都要先做一轮初始化”。

---

## 一个最常见的问题：我需要每次启动时，在项目里初始化，才能用最新 feature 吗

通常 **不需要**。

最短答案是：

- **改代码**：不需要重新初始化
- **改依赖**：需要 `uv sync`，或者让 `uv run` 自动处理
- **第一次进入项目 / 删过环境 / 换了依赖分支**：需要同步一次

如果你的“最新 feature”指的是：

### 1. 你刚改了项目源码

那一般不需要做额外动作，直接：

```bash
uv run python -m yourpkg
```

或者：

```bash
uv run pytest -q
```

就能看到最新代码效果。

---

### 2. 你刚给项目加了一个新依赖

那你要么先显式执行：

```bash
uv add fastapi
```

要么如果是别人已经改好了依赖文件，你执行：

```bash
uv sync
```

这样环境里才会出现这个新包。

---

### 3. 你说的“最新 feature”是别人已经发到 PyPI 的 CLI 工具新版本

那这和项目工作流又是另一回事了。

如果你是用：

```bash
uv tool install chattool
```

把它装成全局工具，那你更新它要走工具升级流程，而不是项目内 `uv sync`。

也就是说：

- 项目源码更新，看项目环境
- CLI 工具升级，看工具环境

这两个不要混在一起。

---

## 场景 7：仓库在 `ChatTool`，日常任务在 `Playground`，怎么配合最好

这个场景非常常见，也很适合 `uv`。

你的实际工作方式可以理解成：

- `ChatTool/` 是源码仓库
- `Playground/` 是日常工作台
- 你会一边给 `ChatTool` 加功能，一边立刻在 `Playground` 里用这些最新能力

这时候，最推荐的思路不是把 `chattool` 当成“全局发布版工具”，而是把 `ChatTool` 仓库当成一个**长期处于开发态的项目环境**。

### 一次性准备

先在仓库目录做一次初始化：

```bash
cd /Users/rexwzh/Documents/Playground/ChatTool
uv python install 3.12
uv sync --extra dev
```

做完之后，`ChatTool/.venv` 里就有一个基于当前源码的开发环境。

---

### 日常从 `Playground` 调用最新源码

如果你每天都在开发和使用 `ChatTool`，**最省力的主路径不是每次都敲 `uv run --project ...`**。

更顺手的做法是：开一个开发终端，激活一次 `ChatTool/.venv`，然后当天都直接用 `chattool`。

```bash
cd /Users/rexwzh/Documents/Playground/ChatTool
uv sync --extra dev
source .venv/bin/activate
```

做完之后，你在这个终端里就可以直接：

```bash
chattool --help
chattool lark info
pytest -q
```

这通常比每次都加 `uv` 更贴近日常使用习惯，也更适合“边开发边调用”的工作流。

---

### 那 `uv run --project ...` 什么时候有价值

它依然有价值，但更适合下面这些情况：

- 你当前 shell 在 `Playground`，不想切目录
- 你在脚本或自动化里显式指定项目环境
- 你临时想从别的目录调用 `ChatTool` 的开发版本

例如：

```bash
uv run --project /Users/rexwzh/Documents/Playground/ChatTool chattool --help
uv run --project /Users/rexwzh/Documents/Playground/ChatTool chattool lark info
```

这个方式的好处是：

- 你当前 shell 还在 `Playground`
- 但命令使用的是 `ChatTool` 项目的 `.venv`
- 读取的是 `ChatTool` 当前源码，而不是某个旧的全局安装版本

所以更准确地说：

- `source .venv/bin/activate`：适合日常开发终端
- `uv run --project ...`：适合跨目录、自动化、偶尔调用

---

### 如果你还是嫌输入重，可以再包一层 alias

如果你经常从 `Playground` 里调用，又不想切目录或激活环境，可以在 `~/.zshrc` 里加：

```bash
alias ctool='uv run --project /Users/rexwzh/Documents/Playground/ChatTool chattool'
```

之后你在 `Playground` 里就可以直接：

```bash
ctool lark info
ctool dns get example.com
```

这样你既保留了“短命令直达”的手感，又不会误用到系统里某个旧版本的 `chattool`。

---

### 改完源码后，要不要重新装

通常不用。

只要你改的是：

- `src/` 里的代码
- 命令实现
- 文档
- 测试

那么 `uv sync --extra dev` 建出来的项目环境会以 editable 方式引用源码，后续你改完代码，再从 `Playground` 里执行：

```bash
uv run --project /Users/rexwzh/Documents/Playground/ChatTool chattool ...
```

看到的就是最新源码行为。

也就是说，对你这种“边开发边用”的模式来说，`uv` 非常合适，因为它天然支持：

- 项目长期维护一个 `.venv`
- 日常在开发终端里直接使用项目环境
- 必要时从别的目录调用这个项目环境
- 不用每改一次功能就重新安装一遍

---

### 什么时候需要再执行一次 `uv sync --extra dev`

一般是这些情况：

- 你改了 `pyproject.toml`
- 你新增了依赖或 extras
- 你切换到依赖不同的分支
- 你删掉了 `.venv`

如果只是普通改功能，不需要每次重新同步。

---

### 什么方式反而不太推荐

如果你现在正持续开发 `ChatTool`，那不太建议把它主要装成：

```bash
uv tool install chattool
```

因为工具环境更适合“稳定使用某个发布版本”，而不是“紧跟本地仓库源码变化”。

对开发态仓库来说，更合适的是：

- `uv sync --extra dev`
- 在开发终端里 `source .venv/bin/activate`
- 需要跨目录时再用 `uv run --project /path/to/ChatTool ...`

也就是：

- 把仓库当项目
- 把 `.venv` 当日常开发入口
- 把 `uv run --project` 当备用入口

---

## 那多个项目之间到底怎么共存

这是从 `conda` 切过来时最容易不安的点。

在 `conda` 里，你常常会直觉地想：

- 项目 A 一个环境
- 项目 B 一个环境
- 每个环境都像一个完整箱子

在 `uv` 里，情况稍微不同：

1. 你可以先装一个 Python 3.12 解释器。
2. 项目 A 用它创建 `A/.venv`。
3. 项目 B 也用它创建 `B/.venv`。
4. 两个项目装不同版本的依赖，彼此互不影响。

也就是说：

- 冲突隔离靠的是“环境”，不是“解释器副本”
- 共享的是 Python 版本和全局缓存
- 不共享的是项目安装结果

因此，`uv` 的多项目共存不是弱，而是更细粒度。

---

## `uv pip install`、`uv add`、`uv tool install` 到底怎么选

这是新手最容易混淆的三个入口。

### `uv add`

适合：

- 你正在一个项目里
- 你希望依赖被记录进 `pyproject.toml`

例子：

```bash
uv add requests
uv add 'httpx>=0.28'
```

---

### `uv pip install`

适合：

- 你已经有一个明确环境
- 你暂时还在沿用 `pip` 风格工作流
- 你不想改项目依赖声明方式

例子：

```bash
uv venv
uv pip install requests
uv pip install 'chattool[dev]'
```

这条路线对老项目过渡非常友好。

---

### `uv tool install`

适合：

- 你想装的是命令行工具
- 你不希望它绑进某个项目
- 你想像系统命令一样长期可用

例子：

```bash
uv tool install ruff
uv tool install 'chattool[dev]'
```

如果只是跑一次，不值得长期安装，那就用：

```bash
uvx ruff check .
uvx --from 'chattool[dev]' chattool --help
```

---

## 用 `chattool[dev]` 举一个最贴近真实开发的例子

我们之前聊过这个问题，因为它刚好能把“包依赖”和“CLI 工具”两种用法分开。

### 情况 1：你只是想像以前一样安装一个包

原来你会这样写：

```bash
pip install 'chattool[dev]'
```

在 `uv` 里，最直接的等价写法是：

```bash
uv pip install 'chattool[dev]'
```

这表示：

- 我有一个当前环境
- 我要把这个包和它的 `dev` extras 装进去

---

### 情况 2：你在做一个 `uv` 项目，想把它作为项目依赖

```bash
uv add 'chattool[dev]'
```

这表示：

- 我不是临时装包
- 我希望依赖写入当前项目的 `pyproject.toml`

---

### 情况 3：你根本不关心项目，只想拿到 `chattool` 命令

```bash
uv tool install 'chattool[dev]'
```

这表示：

- 我想把 `chattool` 当一个长期 CLI 工具来用
- 不想它污染某个项目环境

不过从实际使用上说，`dev` extras 往往是给贡献者准备的。普通使用者如果只是想拿到 `chattool` 命令，通常安装基础包或更有针对性的 extras 会更轻。

如果你只想临时试一下：

```bash
uvx --from 'chattool[dev]' chattool --help
```

---

### 情况 4：你就在 ChatTool 仓库里开发当前项目

如果当前目录就是 ChatTool 仓库，那么你其实更接近“项目开发”场景。对这类仓库，更自然的入口通常是：

```bash
uv sync --extra dev
uv run pytest -q
uv run chattool --help
```

这个思路和“`pip install -e .[dev]`”很接近，但更符合 `uv` 的项目工作流。

---

## `uv` 和 `pip` 的关系：更像“兼容入口”，不是“包装器”

很多人第一次看到 `uv pip install`，会以为它只是帮你调用了 `pip`。

不是。

`uv` 官方明确说明，`uv` 并不会去调用 `pip`，而是自己实现了兼容 `pip` 风格的接口。你可以把 `uv pip` 理解成：

- 帮老工作流迁移
- 帮你先保留 `pip` 心智
- 但底层已经换成 `uv` 自己的解析和安装逻辑

这也是为什么很多场景下，`uv pip install` 会比 `pip install` 更快。

---

## 一个特别常见的误区：没有全局默认环境，是不是很鸡肋

如果你是从 `conda base` 迁移过来，确实会不习惯。

因为 `uv` 默认没有一个“永远自动激活的 base 环境”。

但这并不意味着它没法支持你的工作方式，而是它把场景拆得更清楚：

- 项目依赖，放项目里
- CLI 工具，放工具环境里
- 个人长期环境，自己建 `~/.venvs/default`

这种设计的好处是：

- 不容易把项目依赖和日常工具混在一起
- 不容易把一个大环境越养越脏
- 项目切换更清晰

如果你就是喜欢“有一个自己常用的大环境”，可以保留这个习惯，只是别把它误认为 `uv` 的唯一用法。

---

## `uv` 的开源协议，以及为什么很多人会把 `conda` 误解成“商用工具”

这一点也值得顺手说清楚。

- `uv` 是开源的双许可证项目：`MIT` 或 `Apache-2.0`
- `conda` 包管理器本身也是开源的，许可证是 `BSD-3-Clause`

很多人说“`conda` 是商用的”，通常混淆的是：

- `conda` 这个工具
- `Anaconda Distribution`
- Anaconda 提供的默认仓库和商业条款

也就是说：

- `uv` 本身是开源工具
- `conda` 工具本身也是开源工具
- 商业限制更多发生在 Anaconda 发行版和服务层，而不是 `conda` 命令本身

如果你的目标是“尽量贴近 Python 官方生态、避开额外平台条款、用最轻的方式管理项目”，`uv` 的定位会很自然。

---

## 什么时候选 `uv`，什么时候还该继续用 `conda`

### 更适合 `uv` 的情况

- Web 后端开发
- 普通 Python 包开发
- CLI 工具开发
- 日常脚本和自动化
- 希望统一 `pip`、`venv`、`pipx`、项目依赖管理
- 希望更快

---

### 更适合 `conda` 的情况

- 科学计算和机器学习环境
- 大量依赖二进制库
- 需要 CUDA、MKL、BLAS、R 等复杂运行时
- 你要管理的不只是 Python 包，而是一整套软件环境

一句话总结就是：

- **纯 Python 开发**：优先考虑 `uv`
- **复杂科学计算栈**：`conda` 往往更省心

---

## 最后给一个上手建议

如果你之前主要用 `conda`，不要一开始就强迫自己完全改掉所有习惯。

最平滑的迁移顺序通常是：

1. 先用 `uv python install` 管 Python 版本。
2. 再用 `uvx` 和 `uv tool install` 管日常 CLI 工具。
3. 新项目开始用 `uv init`、`uv add`、`uv run`。
4. 老项目先从 `uv pip install` 过渡，不急着一次性重写。
5. 如果你需要一个“像 base 一样”的长期环境，就自己建 `~/.venvs/default`。

这样迁移，你会逐步发现：

- `uv` 不是强迫你“只能在项目里活着”
- 它只是把“解释器、环境、项目、工具”分得更清楚
- 一旦这个结构想通了，很多之前觉得别扭的地方都会突然顺起来

---

## 参考链接

- 官方首页：<https://docs.astral.sh/uv/>
- 项目指南：<https://docs.astral.sh/uv/guides/projects/>
- Python 安装：<https://docs.astral.sh/uv/guides/install-python/>
- 工具管理：<https://docs.astral.sh/uv/guides/tools/>
- Tools 概念说明：<https://docs.astral.sh/uv/concepts/tools/>
- `uv pip` 文档：<https://docs.astral.sh/uv/pip/>
- Python environments：<https://docs.astral.sh/uv/pip/environments/>
- Scripts 指南：<https://docs.astral.sh/uv/guides/scripts/>
- `conda` 文档：<https://docs.conda.io/docs/>
- `uv` 仓库：<https://github.com/astral-sh/uv>
- `conda` 仓库：<https://github.com/conda/conda>
- Anaconda 法律说明：<https://www.anaconda.com/legal>
