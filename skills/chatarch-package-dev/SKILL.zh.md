---
name: chatarch-package-dev
description: 使用 `chattool pypi init -t chatarch` 创建或维护 ChatArch/chatxxx Python CLI 包，并正确集成外部 `chatstyle` 与 `chatenv`。
version: 0.1.0
---

# ChatArch 包开发

当需要创建或维护独立 ChatArch / chatxxx Python CLI 包时使用这个 skill。

这类包应该能独立安装和发布，不是 ChatTool 插件。

## 从模板开始

```bash
chattool pypi init chatfoo -t chatarch --project-dir ./chatfoo
```

等价 wrapper 写法：

```bash
chatpypi chatfoo -t chatarch --project-dir ./chatfoo
```

只有在确实不需要 docs 或 workflows 时才跳过可选文件：

```bash
chattool pypi init chatfoo -t chatarch --project-dir ./chatfoo --without-mkdocs --without-workflows
```

## 生成物职责

- `src/<module>/cli.py`：Click CLI，使用 ChatStyle-backed 输入解析。
- `src/<module>/__init__.py`：版本号和包入口标记。
- `tests/`：包测试；后续 CLI 行为增加时继续补测试。
- `docs/`：启用 mkdocs 时维护长期文档。
- `mkdocs.yml`：启用 mkdocs 时的文档构建配置。
- `.github/workflows/`：启用 workflows 时的 CI/docs/publish 占位。
- `AGENTS.md`：agent 协作规则。
- `DEVELOP.md`：开发流程与验证说明。
- `CHANGELOG.md`：按日期维护的变更记录。

## ChatStyle 集成

独立 ChatArch 包直接导入 `chatstyle`。不要导入或复制 ChatTool 的 `chattool.interaction` adapter。

对可恢复缺参使用 `CommandSchema`：

```python
import click
from chatstyle import CommandField, CommandSchema, add_interactive_option, resolve_command_inputs

HELLO_SCHEMA = CommandSchema(
    name="hello",
    fields=(CommandField("name", prompt="name", required=True),),
)

@click.group()
def cli() -> None:
    pass

@cli.command()
@click.argument("name", required=False)
@add_interactive_option
def hello(name: str | None, interactive: bool | None) -> None:
    inputs = resolve_command_inputs(
        schema=HELLO_SCHEMA,
        provided={"name": name},
        interactive=interactive,
        usage="Usage: chatfoo hello [NAME] [-i|-I]",
    )
    click.echo(f"Hello, {inputs['name']}!")
```

规则：

- `-i` 强制进入当前命令交互流程。
- `-I` 禁止提示，缺少必填输入时快速失败。
- 对可交互补齐的输入，不要用 Click `required=True` 提前拦截。
- 新的通用 prompt/render/schema 行为应进入 `chatstyle`，不要在业务包里重复实现。

## ChatEnv 集成

使用 `chatenv` 做 typed env/profile 存储。业务包只提供 schema provider。

最小 `src/chatfoo/config.py`：

```python
from chatenv import BaseEnvConfig, EnvField

class FooConfig(BaseEnvConfig):
    _title = "Foo Configuration"
    _aliases = ["foo", "chatfoo"]
    _storage_dir = "Foo"

    FOO_API_BASE = EnvField("FOO_API_BASE", desc="Foo API base URL")
    FOO_API_KEY = EnvField("FOO_API_KEY", desc="Foo API key", is_sensitive=True)
```

在 `pyproject.toml` 注册：

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

## 本地验证

```bash
python -m pytest -q
python -m mkdocs build --strict
chatfoo --help
chatfoo hello ChatArch
chatenv list
chatenv init -t foo
chatenv cat -t foo
```

## 不要做

- 不要把 `chattool.interaction` 复制到独立包。
- 不要让 `chatenv` 硬编码 import 某个业务包。
- 不要把业务 env 字段写进 ChatEnv 包本体。
- 不要把 ChatArch 包描述成 ChatTool 插件。
- scaffold 已存在后，使用 `$chatarch-post-init-dev` 处理持续开发规范。
