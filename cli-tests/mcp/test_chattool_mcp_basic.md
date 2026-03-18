# test_chattool_mcp_basic

测试 `chattool mcp` 的基础链路，覆盖 info/inspect/start 的命令流程。

## 元信息

- 命令：`chattool mcp <command> [args]`
- 目的：验证 MCP 管理 CLI 的基础命令可用。
- 标签：`cli`
- 前置条件：MCP 依赖可用（fastmcp）。
- 环境准备：确保运行环境满足 MCP 要求。
- 回滚：停止服务进程。

## 用例 1：info 输出

- 初始环境准备：
  - MCP 可用。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool mcp info --json-output`，预期输出包含 tools 列表。

参考执行脚本（伪代码）：

```sh
chattool mcp info --json-output
```

## 用例 2：inspect 别名

- 初始环境准备：
  - MCP 可用。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool mcp inspect`，预期输出与 info 等价。

参考执行脚本（伪代码）：

```sh
chattool mcp inspect
```

## 用例 3：start

- 初始环境准备：
  - 选择 stdio 或 http 传输模式。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool mcp start --transport http --port 8000`，预期服务启动。

参考执行脚本（伪代码）：

```sh
chattool mcp start --transport http --port 8000
chattool mcp start --transport stdio
```

## 清理 / 回滚

- 停止服务进程。
