# ChatTool PyPI CLI 设计

> 目标：通过 `chattool pypi` 统一完成 Python 包的构建、校验与发布，让维护者不必手写 `python -m build`、`twine check`、`twine upload` 命令链。

## 设计目标

- 提供统一的 PyPI 发布命令入口，覆盖 build、check、publish 的核心流程。
- 对齐 ChatTool 现有 CLI 规范：缺参自动交互，支持 `-i` / `-I`，敏感信息自动脱敏。
- 默认走安全路径，避免误发正式 PyPI。
- 保持和标准 Python 打包工具兼容，底层继续复用 `build` 与 `twine`。

## 非目标

- 一阶段不自动修改版本号、不自动打 git tag、不自动推送 commit。
- 一阶段不替代 CI 发布流程，主要服务于本地手工发版与排障。

## 适用场景

- 本地验证 `pyproject.toml` 是否可构建。
- 构建 wheel / sdist 并做元数据检查。
- 先发 TestPyPI，再确认后发正式 PyPI。
- 对已有仓库进行发版前自检。

## 代码归位建议

按照当前仓库工具结构，建议新增：

```text
src/chattool/tools/pypi/
├── __init__.py
├── cli.py        # chattool pypi
└── main.py       # build/check/publish 核心逻辑
```

接入方式：

- 在 `src/chattool/client/main.py` 中以 lazy import 方式挂载 `pypi`
- 不需要 MCP 入口
- 与 `setup/` 解耦，避免把打包发布逻辑塞进环境安装模块

## 命令总览（阶段一）

```bash
chattool pypi init
chattool pypi doctor
chattool pypi build
chattool pypi check
chattool pypi publish
chattool pypi release
```

## 默认约定

- 项目目录默认：当前工作目录
- 构建产物目录默认：`dist/`
- 构建配置默认读取：`pyproject.toml`
- 默认发布目标：`testpypi`
- 发布到正式 `pypi` 时必须显式指定 `--repository pypi`
- 所有认证信息默认复用标准 `twine` 生态，不额外发明私有协议

## 命令设计

### 1) `chattool pypi init`

- 作用：生成一个最小可发布的 `src/` 布局 Python 包骨架
- 默认行为：
  - 缺少包名时自动进入向导
  - `-i` 进入完整交互，按顺序补全 `Package name`、`project_dir`、`description`、`requires_python`、`license`、`author`、`email`
  - 所有 prompt 展示实际默认值
  - 生成的项目可直接运行 `python -m pytest -q`

建议选项：

- `NAME`
- `--project-dir PATH`
- `--description TEXT`
- `--python SPEC`
- `--license TEXT`
- `--author TEXT`
- `--email TEXT`
- `-i/--interactive`
- `-I/--no-interactive`

输出重点：

- 创建后的项目目录
- 规范化后的模块名
- 生成文件列表

### 2) `chattool pypi doctor`

- 作用：发版前自检
- 检查项：
  - `pyproject.toml` 是否存在
  - `project.name`、`readme`、`requires-python`、`license` 等关键字段是否可读
  - 动态版本是否可解析
  - `README.md`、`LICENSE` 是否存在
  - `build`、`twine` 是否已安装
  - `dist/` 是否存在旧产物
- 输出：
  - 列表式检查结果
  - 失败原因
  - 下一步建议

建议选项：

- `--project-dir PATH`
- `--dist-dir PATH`
- `-i/--interactive`
- `-I/--no-interactive`

### 3) `chattool pypi build`

- 作用：生成 wheel / sdist
- 默认行为：
  - 默认先清理目标 `dist/` 目录中的旧构建产物
  - 默认同时构建 `sdist` 与 `wheel`
  - 调用底层 `python -m build`

建议选项：

- `--project-dir PATH`
- `--dist-dir PATH`
- `--sdist`
- `--wheel`
- `--clean/--no-clean`
- `-i/--interactive`
- `-I/--no-interactive`

行为约束：

- 若 `pyproject.toml` 缺失，直接失败
- 若指定 `-i`，提示 `project_dir`、`dist_dir`、`build_target`、`clean`
- 若指定 `-I`，不进入交互

### 4) `chattool pypi check`

- 作用：检查构建产物元数据与长描述
- 默认行为：
  - 若 `dist/` 不存在，提示先执行 `chattool pypi build`
  - 调用底层 `twine check dist/*`

建议选项：

- `--project-dir PATH`
- `--dist-dir PATH`
- `--strict`

输出重点：

- 哪些文件被检查
- 哪些元数据失败
- README 渲染或 metadata 问题的定位提示
- 若指定 `-i`，提示 `project_dir`、`dist_dir`、`strict`

### 5) `chattool pypi publish`

- 作用：上传构建产物到 TestPyPI 或 PyPI
- 默认行为：
  - 默认目标仓库为 `testpypi`
  - 默认要求先有可用构建产物
  - 认证优先复用 `.pypirc` 或 `TWINE_USERNAME` / `TWINE_PASSWORD`
  - 若进入交互，可提示输入 token，但回显必须脱敏

建议选项：

- `--project-dir PATH`
- `--dist-dir PATH`
- `--repository [testpypi|pypi]`
- `--repository-url URL`
- `--skip-existing`
- `--yes`
- `-i/--interactive`
- `-I/--no-interactive`

安全策略：

- 发布到 `pypi` 时，如果没有 `--yes`，必须二次确认
- 若当前目录仍有未处理构建失败痕迹，可提示用户先 `build` / `check`
- 不在日志中打印 token 明文
- 若指定 `-i`，提示目录、仓库、上传参数与凭证默认值

### 6) `chattool pypi release`

- 作用：串联 `build -> check -> publish`
- 默认行为：
  - 默认发布到 `testpypi`
  - 执行前打印完整计划
  - 任何一步失败则中断

建议选项：

- `--project-dir PATH`
- `--dist-dir PATH`
- `--repository [testpypi|pypi]`
- `--skip-existing`
- `--yes`
- `--dry-run`
- `-i/--interactive`
- `-I/--no-interactive`

说明：

- 这是面向高频发版路径的快捷命令
- 一阶段不做版本递增，只消费当前仓库已有版本
- 若指定 `-i`，提示目录、构建参数、检查参数、发布参数与凭证默认值

## 交互式流程（草案）

```text
chattool pypi release -i
1) 识别项目目录和 pyproject.toml
2) 解析当前包名与版本
3) 选择目标仓库: testpypi / pypi
4) 检查认证来源: .pypirc / 环境变量 / 手动输入
5) 确认是否清理旧 dist 产物
6) 执行 build
7) 执行 twine check
8) 输出待上传文件清单并确认发布
```

## 认证与配置策略

优先顺序建议如下：

1. 显式 CLI 参数
2. `.pypirc`
3. `TWINE_USERNAME` / `TWINE_PASSWORD`
4. 交互式输入

设计原则：

- 复用标准 Python 发布生态，避免引入 ChatTool 私有认证格式
- 命令输出中只显示脱敏后的用户名或 token 前后缀
- 若用户选择交互输入 token，一阶段默认只用于本次命令，不自动持久化

## 典型用法

### 构建并检查

```bash
chattool pypi build
chattool pypi check
```

### 先发 TestPyPI

```bash
chattool pypi release --repository testpypi
```

### 发正式 PyPI

```bash
chattool pypi publish --repository pypi --yes
```

## 与当前仓库的关系

当前仓库已经具备 `pyproject.toml`、`build`、`twine`、`README.md`、`LICENSE` 等基础条件，因此新增 `chattool pypi` 的价值主要在于：

- 收敛重复的发版命令
- 统一交互体验与错误提示
- 降低新维护者的发布门槛
- 为后续 CI/CD 与 doc-first CLI 测试提供稳定接口

## 后续实现建议

- 底层命令封装放在 `src/chattool/tools/pypi/main.py`
- `cli.py` 只处理参数、交互与输出展示
- 构建与上传相关 import 放到函数内部，保持 CLI 冷启动速度
- 为 `cli-tests/` 新增 `test_chattool_pypi_basic.md`
- 正式实现时补充：
  - `tests/tools/pypi/` 单元测试
  - `cli-tests/pypi/` doc-first CLI 测试
  - `docs/tools/` 下的正式用户文档

## 结论

`chattool pypi` 最适合作为一个轻量、可审阅、默认安全的发布编排 CLI：

- `doctor` 负责发现问题
- `build` / `check` 负责产物质量
- `publish` / `release` 负责发版流程

这样既不破坏标准 Python 打包生态，也能让 ChatTool 的发版能力符合项目现有 CLI 风格。
