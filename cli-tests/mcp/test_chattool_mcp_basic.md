# chattool mcp 基础用例

## 元信息

- 命令：`chattool mcp <command> [options]`
- 目的：验证 mcp CLI 的基础信息与别名命令可用。
- 标签：`cli`
- 前置条件：无
- 环境准备：无
- 回滚：无
- 来源：`tests/mcp/test_mcp_cli.py`

## 状态

- TODO：需要确认真实 MCP 服务可用性与最小配置要求。

## 用例 1：info JSON 输出

### 初始环境准备

- 启动 MCP 服务或确保本地默认可用。

### 相关文件

- 无

### 预期过程和结果

1. 执行 `chattool mcp info --json-output`，预期输出为 JSON 且包含工具列表。

### 参考执行脚本（伪代码）

```sh
chattool mcp info --json-output
```

### 清理 / 回滚

- 无

## 用例 2：inspect 别名命令

### 初始环境准备

- MCP 服务可用。

### 相关文件

- 无

### 预期过程和结果

1. 执行 `chattool mcp inspect`，预期输出包含 MCP Server 信息。

### 参考执行脚本（伪代码）

```sh
chattool mcp inspect
```

### 清理 / 回滚

- 无
