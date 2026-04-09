# ChatTool CLI 交互规范设计

## 背景

ChatTool 的 CLI 长期存在两套并行模式：

- 一部分命令把缺参恢复、TTY 检查和 prompt 流程手写在 callback 里。
- 另一部分命令直接依赖 Click 的 `required=True` 或默认必填位置参数。

后者会在进入命令函数之前就被 Click 拦截，导致统一的交互机制根本没有机会运行。随着命令数量增加，这会带来几个持续问题：

- 缺参时的行为不一致，有的命令自动补问，有的直接报错。
- `-i/-I` 语义不统一。
- 同类命令重复维护 `missing_required`、TTY 判断和 prompt 样板。
- CLI 测试需要为每个命令单独 mock 一套交互控制流。

这一轮重构的目标，就是把“可恢复缺参默认进入交互”变成默认机制，而不是靠每个命令手动记住这条规范。

## 目标

- 让新 CLI 命令默认走统一交互机制。
- 统一 `-i` / `-I` 语义。
- 避免 Click 在 callback 执行前就拦截可恢复缺参。
- 让命令实现更接近“声明输入结构 + 执行业务逻辑”。
- 让 mock CLI 测试聚焦在共享 resolver，而不是散落在各个命令的私有 helper 里。

## 非目标

- 不重写整套 Click CLI 框架。
- 不要求所有命令都必须做成向导式入口页。
- 不强制把所有业务逻辑迁入 `interaction` 模块。

## 设计原则

### 1. 命令优先，交互兜底

命令行参数仍然是第一输入方式。只有当必要参数缺失，且该缺失是可恢复的，才自动进入交互补全。

### 2. 默认行为一致

- 缺参时：默认自动补问。
- `-i`：强制进入当前命令的交互补参流程。
- `-I`：完全禁用交互；若缺参则直接报错。

### 3. 业务逻辑与输入编排分离

命令 callback 尽量只做三件事：

1. 接入 Click 参数
2. 调用共享 resolver 拿到完整输入
3. 执行业务逻辑

### 4. 最小迁移成本

保留 Click 命令结构，不引入过重的 decorator 黑魔法。优先通过轻量 schema + resolver 的方式逐步迁移。

## 共享机制

位置：`src/chattool/interaction/command_schema.py`

提供以下共享对象：

- `CommandField`
- `CommandSchema`
- `CommandConstraint`
- `resolve_command_inputs()`
- `add_interactive_option()`

### `CommandField`

描述单个命令输入字段，例如：

- 名称
- prompt 文案
- 类型（text/path/int/select/confirm）
- 是否必填
- 默认值
- 是否在“缺失时”自动补问
- 自定义校验与 normalizer

### `CommandConstraint`

描述跨字段约束，例如：

- `full_domain` 或 `domain + rr` 二选一
- `KEY=VALUE` 必须包含 `=`

这类逻辑不适合继续散落在 callback 的多段 if/else 中。

### `resolve_command_inputs()`

统一负责：

- 收集当前命令收到的参数
- 判定缺参
- 执行 `-i/-I` 语义
- 判断当前是否可交互
- 自动补问缺失字段
- 执行字段/约束校验
- 返回最终可执行输入

## 实现约定

### 1. 可恢复缺参不要继续用 Click 必填拦截

对于会通过交互恢复的参数：

- 不要再写 `@click.option(..., required=True)`
- 不要再使用默认必填位置参数

正确做法是：

- Click 层尽量用 `required=False`
- 在 schema 中声明 `required=True`
- 由 resolver 统一处理缺参补问和报错

### 2. 命令默认接入共享 `-i/-I`

通过 `@add_interactive_option` 注入统一开关，避免每个命令重复定义文案和参数名。

### 3. 命令专属 helper 只保留业务语义转换

允许存在少量 helper，但它们应只处理业务归一化，例如：

- `full_domain -> domain/rr`
- 读取并归一化 repo/path

不要再让命令专属 helper 承载通用的 interactive 控制流。

## 推荐写法

```python
from chattool.interaction import (
    CommandField,
    CommandSchema,
    add_interactive_option,
    resolve_command_inputs,
)


MY_SCHEMA = CommandSchema(
    name="demo",
    fields=(
        CommandField("name", prompt="name", required=True),
        CommandField("output", prompt="output path", kind="path", default="./out.txt"),
    ),
)


@click.command()
@click.option("--name", required=False)
@click.option("--output", required=False)
@add_interactive_option
def demo(name, output, interactive):
    inputs = resolve_command_inputs(
        schema=MY_SCHEMA,
        provided={"name": name, "output": output},
        interactive=interactive,
        usage="Usage: chattool demo [--name TEXT] [--output PATH] [-i|-I]",
    )
    run_demo(inputs["name"], inputs["output"])
```

## 已落地命令

这一轮已经迁移的代表命令包括：

- `chattool dns`
- `chattool client cert`
- `chattool client svg2gif`
- `chattool gh`
- `chattool zulip`
- `chattool image`
- `chatenv` 高频 profile/key/test 命令
- `chattool explore arxiv get`
- `chattool network ping`
- `chattool tplogin ufw add`

这些命令可以作为后续新增 CLI 的直接参考实现。

## 测试规范

- 涉及 CLI 行为的改动，继续保持 doc-first。
- mock 驱动的 CLI 行为测试统一放在 `mock-cli-tests/`。
- 优先测试共享行为：
  - 缺参自动补问
  - `-i` 强制交互
  - `-I` 禁用交互
  - 非 TTY 场景直接报错

## 收益

与旧模式相比，这套机制的收益是：

- 新命令默认更容易写对
- CLI 行为更一致
- 测试点更集中
- 迁移可渐进完成，不需要重写整套 CLI 架构

## 例外

如果某个参数缺失后不适合恢复，或者交互补问会明显增加歧义，可以保留为显式报错。但这应是明确例外，而不是默认做法。
