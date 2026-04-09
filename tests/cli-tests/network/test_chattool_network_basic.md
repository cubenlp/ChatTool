# test_chattool_network_basic

测试 `chattool network` 的基础链路，覆盖 ping/ssh/links/services 的命令流程。

## 元信息

- 命令：`chattool network <command> [args]`
- 目的：验证网络扫描 CLI 的核心命令可用。
- 标签：`cli`
- 前置条件：网络访问与目标环境可用。
- 环境准备：按需准备网络段、IP 列表与服务 URL。
- 回滚：删除输出文件。

## 用例 1：ping 扫描

- 初始环境准备：
  - 准备可访问网段。
- 相关文件：
  - `<tmp>/ping.txt`

预期过程和结果：
  1. 执行 `chattool network ping --network 192.168.1.0/24 --output <path>`，预期输出存活主机列表。

参考执行脚本（伪代码）：

```sh
chattool network ping --network 192.168.1.0/24 --output /tmp/ping.txt
```

## 用例 2：ssh 扫描

- 初始环境准备：
  - 准备 IP 列表文件或网段。
- 相关文件：
  - `<tmp>/ssh.txt`

预期过程和结果：
  1. 执行 `chattool network ssh --network 192.168.1.0/24 --port 22 --output <path>`，预期输出可达主机。

参考执行脚本（伪代码）：

```sh
chattool network ssh --network 192.168.1.0/24 --port 22 --output /tmp/ssh.txt
chattool network ssh --input /tmp/ip-list.txt --port 22 --output /tmp/ssh.txt
```

## 用例 3：links 检查

- 初始环境准备：
  - 准备可访问 URL。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool network links --url http://example.com`，预期输出检测结果。

参考执行脚本（伪代码）：

```sh
chattool network links --url http://example.com
chattool network links --path . --glob "*.md"
```

## 用例 4：services 检查

- 初始环境准备：
  - 配置 `CHATTOOL_CHROMIUM_URL`、`CHATTOOL_CHROMEDRIVER_URL`、`CHATTOOL_PLAYWRIGHT_URL`。
  - 如需 token，配置 `CHATTOOL_CHROMIUM_TOKEN`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool network services`，预期输出服务状态。

参考执行脚本（伪代码）：

```sh
chattool network services
```

## 清理 / 回滚

- 删除输出文件。
