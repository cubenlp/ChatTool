# test_leand_sync_manual

测试 `leand sync` 的手工验收与真实链路约定：重点覆盖编译复用、依赖自动刷新、缺失文件错误和多仓库会话分配。

## 01. 复用编译的能力

- 初始环境准备：
  - 工作目录：仓库根目录 `/opt/tiger/leand4`
  - 初始状态：执行 `leandev restart`，重建 broker 到初始状态
- 相关文件：
  - `DemoRepo/DemoRepoTest/manual/test.lean`: `#eval IO.sleep 3000\n\n#eval "hello"`

预期过程和结果：
  1. 执行 `leandev restart`，broker 重建到干净状态，`leandev health` 正常。
  2. 执行 `leand sync DemoRepo/DemoRepoTest/manual/test.lean`，预期返回 `hello`；第一次执行允许包含冷启动与首轮编译成本，不要求时间 < 3s。
  3. 更新文件 `DemoRepo/DemoRepoTest/manual/test.lean` 为 `#eval IO.sleep 3000\n\n#eval "hi"`。
  4. 再次执行 `leand sync DemoRepo/DemoRepoTest/manual/test.lean`，预期返回 `hi`，并体现已复用现有会话，整体时间 < 3s。
  5. 重置文件 `DemoRepo/DemoRepoTest/manual/test.lean` 为原始内容 `#eval IO.sleep 3000\n\n#eval "hello"`，避免污染仓库。
  6. 第三次执行 `leand sync DemoRepo/DemoRepoTest/manual/test.lean`，预期重新返回 `hello`，且时间仍然 < 3s。
  7. 执行 `leandev stop` 完成用例清理。

参考执行脚本（伪代码）：

```sh
leandev restart
leandev health
time leand sync DemoRepo/DemoRepoTest/manual/test.lean
# update: hello => hi
time leand sync DemoRepo/DemoRepoTest/manual/test.lean
# reset: hi => hello
time leand sync DemoRepo/DemoRepoTest/manual/test.lean
leandev stop
```

## 02. 自动 stale 机制

- 初始环境准备：
  - 工作目录：仓库根目录 `/opt/tiger/leand4`
  - 初始状态：执行 `leandev restart`，重建 broker 到初始状态
- 相关文件：
  - `DemoRepo/DemoRepoTest/manual/test1.lean`: `def a := 1`
  - `DemoRepo/DemoRepoTest/manual/test2.lean`: `import DemoRepoTest.manual.test1\n\n#eval a`

预期过程和结果：
  1. 执行 `leandev restart`，broker 重建到干净状态，`leandev health` 正常。
  2. 执行 `leand sync DemoRepo/DemoRepoTest/manual/test2.lean`，预期返回 `1`，说明当前依赖链初始状态正确。
  3. 更新文件 `DemoRepo/DemoRepoTest/manual/test1.lean` 为 `def a := 3`。
  4. 再次执行 `leand sync DemoRepo/DemoRepoTest/manual/test2.lean`，预期直接返回 `3`，说明 broker 能在同一会话内感知依赖变化并刷新结果。
  5. 重置文件 `DemoRepo/DemoRepoTest/manual/test1.lean` 为 `def a := 1`，避免污染仓库。
  6. 第三次执行 `leand sync DemoRepo/DemoRepoTest/manual/test2.lean`，预期返回 `1`，说明恢复后的结果也能被正确感知。
  7. 执行 `leandev stop` 完成用例清理。

参考执行脚本（伪代码）：

```sh
leandev restart
leandev health
leand sync DemoRepo/DemoRepoTest/manual/test2.lean
# update: test1.lean => def a := 3
leand sync DemoRepo/DemoRepoTest/manual/test2.lean
# reset: test1.lean => def a := 1
leand sync DemoRepo/DemoRepoTest/manual/test2.lean
leandev stop
```

## 03. 缺失文件返回错误

- 初始环境准备：
  - 工作目录：仓库根目录 `/opt/tiger/leand4`
  - 初始状态：执行 `leandev restart`，重建 broker 到初始状态
- 相关文件：`DemoRepo/missing_file.lean` 不存在

预期过程和结果：
  1. 执行 `leandev restart`，broker 重建到干净状态，`leandev health` 正常。
  2. 执行 `leand sync DemoRepo/missing_file.lean`，预期返回稳定错误 `Lean file does not exist`，并以非零退出码结束。
  3. 执行 `leandev stop` 完成用例清理。

参考执行脚本（伪代码）：

```sh
leandev restart
leandev health
leand sync DemoRepo/missing_file.lean
leandev stop
```

## 04. 多目录机制

这是这次代码重构的动机来源，支持不同仓库下，自动分配不同的 LSP。

- 初始环境准备：
  - 工作目录：CLI 执行位置不固定；这里以仓库根目录 `/opt/tiger/leand4` 为例
  - 初始状态：执行 `leandev restart`，重建 broker 到初始状态
- 相关仓库：`DemoRepo` 和 `SubWorktree`

预期过程和结果：
  1. 执行 `leandev restart`，broker 重建到干净状态，`leandev health` 正常。
  2. 在当前工作目录下执行 `leand sync DemoRepo/DemoRepo/Basic.lean`，预期返回 `ℕ`，并且 `root_path` 被解析为 `DemoRepo` 的绝对路径。
  3. 读取一次 `leandev health`，预期 `session_count=1`，说明 broker 为第一个仓库创建了一个会话。
  4. 继续执行 `leand sync SubWorktree/SubWorktree/Basic.lean`，预期返回 `world`，并且 `root_path` 被解析为 `SubWorktree` 的绝对路径。
  5. 再次读取 `leandev health`，预期 `session_count=2`，说明 broker 已分别为两个不同仓库分配并保留独立 LSP 会话。
  6. 执行 `leandev stop` 完成用例清理。

参考执行脚本（伪代码）：

```sh
leandev restart
leandev health
leand sync DemoRepo/DemoRepo/Basic.lean
leandev health
leand sync SubWorktree/SubWorktree/Basic.lean
leandev health
leandev stop
```

# CLI Tests 文档模板

本文件是 cli-tests 的文档先行模板。每个 cli 测试都应从这里开始。

## 元信息

- 命令：`chattool <tool> <command> [args]`
- 目的：一句话说明该测试验证什么。
- 标签：`cli`，可选 `integration`，可选工具标签（如 `lark`）。
- 前置条件：需要的环境变量、凭证或服务。
- 环境准备：如何恢复到可复现的初始状态。
- 回滚：如何清理或恢复测试产生的变更。

## 用例 1：<用例标题>

### 初始环境

- 描述初始状态，简洁且可复现。

### 相关文件

- 列出该用例会创建/改写的文件。

### 步骤与预期

1. 执行 <动作 A>，预期 <结果 A>。
2. 执行 <动作 B>，预期 <结果 B>。
3. 执行 <动作 C>，预期 <结果 C>。

### 伪代码（sh）

```sh
# 仅示例，需替换为真实命令
chattool <tool> <command> --help
chattool <tool> <command> <args>
```

### 清理 / 回滚

- 描述如何恢复改动。必要时在测试中使用 try/finally。

## 说明

- 文档先行：先更新本 `.md`，再实现对应 `.py`。
- 如文档与测试不一致，先更新文档并说明原因。
