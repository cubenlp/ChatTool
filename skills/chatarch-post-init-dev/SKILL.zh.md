---
name: chatarch-post-init-dev
description: 在独立 `chatpypi init -t chatarch` 创建项目后继续开发，保持 chatenv schema、chatstyle 交互式 CLI、文档、测试和 changelog 对齐。
version: 0.1.0
---

# ChatArch 初始化后开发规范

当 ChatArch / chatxxx 项目已经通过 `chatpypi <name> -t chatarch` 或 `chatpypi init <name> -t chatarch` 生成后，使用这个 skill 指导后续开发。

目标：把 scaffold 继续扩展成可维护的 ChatArch 包，同时不偏离共享的 `chatstyle` 和 `chatenv` 约定。

## 先检查 scaffold

在生成项目根目录运行：

```bash
python -m pytest -q
python -m mkdocs build --strict
<cli-name> --help
```

扩展功能前确认这些文件存在：

- `AGENTS.md`：新仓库的 agent 协作规则。
- `DEVELOP.md`：本地开发流程。
- `CHANGELOG.md`：按日期维护的变更记录。
- `src/<module>/cli.py`：CLI 入口。
- `tests/`：生成的 smoke tests 和后续行为测试。
- `docs/` 与 `mkdocs.yml`：启用 mkdocs 时的文档面。

## 用 ChatStyle 维护 CLI 行为

独立 ChatArch 包直接使用 `chatstyle`。不要从这些项目里导入 `chattool.interaction`。

开发规则：

- 用 `CommandSchema` 和 `CommandField` 描述可恢复的命令输入。
- 支持 `-i/-I` 的命令加 `@add_interactive_option`。
- 用 `resolve_command_inputs()` 解析参数。
- 对可交互补齐的值，不要用 Click `required=True` 提前拦截。
- prompt 默认值必须和实际执行默认值一致。
- 敏感值在 prompt 和输出中必须脱敏。
- 可复用的 prompt/render/schema 改进应上游进入 `chatstyle`，不要沉淀在业务包里。

最小模式：

```python
from chatstyle import CommandField, CommandSchema, add_interactive_option, resolve_command_inputs

RUN_SCHEMA = CommandSchema(
    name="run",
    fields=(CommandField("target", prompt="target", required=True),),
)

@cli.command()
@click.argument("target", required=False)
@add_interactive_option
def run(target: str | None, interactive: bool | None) -> None:
    inputs = resolve_command_inputs(
        schema=RUN_SCHEMA,
        provided={"target": target},
        interactive=interactive,
        usage="Usage: chatfoo run [TARGET] [-i|-I]",
    )
    ...
```

## 用 ChatEnv 维护配置

配置 schema 保留在业务包中，通过 entry point 让 `chatenv` 发现。

开发规则：

- 在 `src/<module>/config.py` 或小型 config package 中定义 provider schema。
- 从 `chatenv` 导入 `BaseEnvConfig` 和 `EnvField`。
- 用 `_aliases` 提供用户可输入的 `-t` selector。
- 用 `_storage_dir` 指定 `$CHATARCH_HOME/envs/` 下的目录。
- secret 字段设置 `is_sensitive=True`。
- 在 `[project.entry-points."chatenv.configs"]` 下注册 provider。
- 除非有很强的包特定理由，不要新增独立 env CLI。

最小 schema：

```python
from chatenv import BaseEnvConfig, EnvField

class FooConfig(BaseEnvConfig):
    _title = "Foo Configuration"
    _aliases = ["foo", "chatfoo"]
    _storage_dir = "Foo"

    FOO_API_BASE = EnvField("FOO_API_BASE", desc="Foo API base URL")
    FOO_API_KEY = EnvField("FOO_API_KEY", desc="Foo API key", is_sensitive=True)
```

entry point：

```toml
[project.entry-points."chatenv.configs"]
chatfoo = "chatfoo.config"
```

把包安装到当前环境后验证：

```bash
chatenv list
chatenv init -t foo
chatenv cat -t foo
chatenv paste --stdin --profile work
```

## 开发循环

每增加一个行为：

1. 更新 `src/<module>/` 下的 CLI/API 代码。
2. 在 `tests/` 下增加或调整测试。
3. 用户可见行为同步更新 `docs/`。
4. quickstart 变化时更新 `README.md`。
5. 在 `CHANGELOG.md` 追加日期记录。
6. 交付前运行验证。

推荐验证：

```bash
python -m pytest -q
python -m mkdocs build --strict
<cli-name> --help
<cli-name> <command> --help
<cli-name> <command> -I
chatenv list
```

用 `-I` 检查非交互失败路径不会卡住。

## Review 清单

开 PR 或更新 PR 前确认：

- 支持交互补参的 CLI 命令暴露 `-i/-I`。
- 缺参时要么正确 prompt，要么在 `-I` 下快速失败。
- 独立包没有导入 `chattool.interaction`。
- config schema 通过 `chatenv.configs` 注册。
- 敏感 env 值已脱敏。
- tests、docs、README 和 `CHANGELOG.md` 已反映变更。
- `python -m pytest -q` 和 `python -m mkdocs build --strict` 通过。
