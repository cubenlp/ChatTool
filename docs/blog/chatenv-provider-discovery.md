# ChatArch 设计笔记｜chatenv 如何发现 chatxxx 模块的配置？

这次把 env/profile 能力从 ChatTool 中抽到 ChatEnv 后，最容易混淆的问题是：

**`chatenv` 是一个独立 CLI，但具体配置定义在 `chattool`、`chatdns`、`chatfoo` 这些业务包里。那 `chatenv` 怎么知道有哪些配置类型？**

答案是：`chatenv` 不发现“命令”，它只发现“配置 provider”。

- CLI 命令固定由 `chatenv` 提供，例如 `list/cat/init/new/save/use/delete/paste/test`；
- 业务包只负责声明自己的 typed env schema，例如 `OpenAIConfig`、`TencentConfig`；
- 两者通过 Python package entry point 连接，entry point 的 group 是 `chatenv.configs`。

这样做之后，`chatxxx` 系列项目不用各自复制一套 env CLI，只要注册 schema，统一走 `chatenv`。

---

## 先看一个最小例子

假设我们有一个业务包 `chatfoo`，希望把 Foo 服务的密钥接入 ChatEnv。

第一步，在 `chatfoo/config.py` 里定义 schema：

```python
from chatenv import BaseEnvConfig, EnvField


class FooConfig(BaseEnvConfig):
    _title = "Foo Configuration"
    _aliases = ["foo", "chatfoo"]
    _storage_dir = "Foo"

    FOO_API_BASE = EnvField("FOO_API_BASE", desc="Foo API base URL")
    FOO_API_KEY = EnvField("FOO_API_KEY", desc="Foo API key", is_sensitive=True)

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        # 这里写 chatfoo 自己的连通性验证。
        print("✅ Success!")
```

第二步，在 `chatfoo/pyproject.toml` 注册 entry point：

```toml
[project]
dependencies = [
    "chatenv>=0.1.1",
]

[project.entry-points."chatenv.configs"]
chatfoo = "chatfoo.config"
```

安装 `chatfoo` 后，用户就可以直接用：

```bash
chatenv init -t foo
chatenv cat -t foo
chatenv new -t foo work
chatenv use -t foo work
chatenv test -t foo
```

注意：这里没有 `chatfoo env`，也没有 `chatenv` 硬编码 import `chatfoo`。

---

## `entry_points()` 到底做了什么？

在 ChatEnv 里，provider discovery 的核心逻辑是：

```python
from importlib.metadata import entry_points

for ep in entry_points(group="chatenv.configs"):
    ep.load()
```

这段代码不是在调用某个 CLI，也不是在执行业务命令。它做的是：

1. 从当前 Python 环境里已安装包的 metadata 中，找出所有声明在 `chatenv.configs` 组下的入口；
2. 得到类似 `chatfoo = "chatfoo.config"` 的记录；
3. 对每条记录调用 `ep.load()`；
4. `ep.load()` 会 import `chatfoo.config` 模块。

也就是说，entry point 是一种“安装后可发现的 import 声明”。业务包通过 `pyproject.toml` 告诉外部工具：

> 如果你要加载我的 ChatEnv 配置，请 import 这个模块。

你可以用下面的命令查看当前环境里有哪些 provider：

```bash
python - <<'PY'
from importlib.metadata import entry_points

for ep in entry_points(group="chatenv.configs"):
    print(ep.name, "=>", ep.value)
PY
```

---

## 为什么 import 模块就完成注册？

关键在 `BaseEnvConfig.__init_subclass__`。

ChatEnv 的基类大致是这样：

```python
class BaseEnvConfig:
    _registry = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls not in BaseEnvConfig._registry:
            BaseEnvConfig._registry.append(cls)
```

当 Python import `chatfoo.config` 时，模块里的类定义会被执行：

```python
class FooConfig(BaseEnvConfig):
    ...
```

类创建完成后，Python 自动触发 `BaseEnvConfig.__init_subclass__`，于是 `FooConfig` 被加入 `BaseEnvConfig._registry`。

所以完整链路是：

```text
entry point 找到 chatfoo.config
  -> ep.load() import chatfoo.config
  -> Python 执行 FooConfig 类定义
  -> BaseEnvConfig.__init_subclass__ 自动注册 FooConfig
  -> chatenv CLI 可以从 registry 解析 -t foo
```

这就是为什么 `chatenv` 本身不需要知道 `chatfoo` 的存在。

---

## `chatenv cat -t foo` 的完整流程

以这条命令为例：

```bash
chatenv cat -t foo
```

运行时流程可以理解为：

```text
chatenv cat -t foo
  -> 进入 chatenv.cli
  -> load_config_providers()
  -> entry_points(group="chatenv.configs")
  -> ep.load() imports chatfoo.config
  -> FooConfig 注册到 BaseEnvConfig._registry
  -> resolve_config_types(("foo",)) 匹配 _aliases / _storage_dir / _title
  -> EnvStore 读取 ~/.chatarch/envs/Foo/.env
  -> 按 FooConfig.get_fields() 输出字段
```

这里 CLI 逻辑完全是通用的：

- `cat` 不知道 `FOO_API_KEY` 是什么；
- `paste` 不知道 Foo 服务怎么用；
- `test` 只负责找到 `FooConfig`，具体测试逻辑由 `FooConfig.test()` 实现。

这样可以把“通用 env/profile 操作”和“业务服务含义”分开。

---

## 当前 ChatTool 是怎么接入的？

ChatTool 现在就是一个 ChatEnv consumer。

在 `pyproject.toml` 中注册：

```toml
[project.entry-points."chatenv.configs"]
chattool = "chattool.config"
```

在 `src/chattool/config/__init__.py` 中统一导出配置类。具体 schema 按类型拆到独立文件，例如 `src/chattool/config/openai.py`、`src/chattool/config/feishu.py`：

```python
from chatenv.fields import BaseEnvConfig, EnvField


class OpenAIConfig(BaseEnvConfig):
    _title = "OpenAI Configuration"
    _aliases = ["oai", "openai"]
    _storage_dir = "OpenAI"

    OPENAI_API_BASE = EnvField("OPENAI_API_BASE", desc="The base url of the API")
    OPENAI_API_KEY = EnvField("OPENAI_API_KEY", desc="Your API key", is_sensitive=True)
    OPENAI_API_MODEL = EnvField("OPENAI_API_MODEL", default="gpt-5.5")

    @classmethod
    def test(cls):
        ...
```

于是安装当前分支的 ChatTool 后，`chatenv` 能发现 ChatTool 的配置类型：

```bash
chatenv list
chatenv cat -t oai
chatenv paste
chatenv test -t oai
```

`chatenv` 只负责统一 CLI 和文件读写；OpenAI、Feishu、DNS、CRS 等具体变量仍由 ChatTool 自己维护。

---

## 业务包开发者应该怎么做？

一个新的 `chatxxx` 项目如果要接入 ChatEnv，只需要做四件事：

1. 依赖 `chatenv`；
2. 定义 `BaseEnvConfig` 子类；
3. 在 `pyproject.toml` 注册 `chatenv.configs` entry point；
4. 如有需要，实现 schema 自己的 `test()`。

不应该做的事：

- 不要在每个业务包里重写 `env list/cat/paste`；
- 不要让 `chatenv` 硬编码 import 某个业务包；
- 不要把业务变量写进 ChatEnv；
- 不要保留 `chattool env` 作为新的主入口。

长期看，`chatenv` 是 ChatArch 系列的底层 env/profile CLI。`chattool`、`chatdns`、`chatstyle` 等项目各自提供能力和 schema，统一被 ChatArch 工具链发现和组合。

---

## 和后续能力发现的关系

`chatenv.configs` 目前只解决一件事：发现 env schema。

未来如果要把 DNS、证书、MCP、serve backend 这些能力也做成可发现、可注册的形式，可以沿用同一类机制，但应该使用新的 entry point group，例如：

```toml
[project.entry-points."chatarch.capabilities"]
chatdns = "chatdns.capabilities"
```

也就是说，entry point 是一种通用的“插件发现”方式；`chatenv.configs` 是它在 env/profile 领域的一个具体应用。

当前阶段先把 env 这条链路跑通：

```text
纯代码 schema
  -> entry point provider
  -> chatenv CLI
  -> ~/.chatarch/envs typed profiles
```

这个基础稳定后，再把同样的思想迁移到 serve/MCP/backend 能力注册上，会更自然。
