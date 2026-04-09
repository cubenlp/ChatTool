# test_chattool_client_basic

测试 `chattool client` 的基础链路，覆盖证书客户端与 svg2gif 客户端入口。

## 元信息

- 命令：`chattool client <command> [args]`
- 目的：验证远程客户端命令的基础可用性。
- 标签：`cli`
- 前置条件：服务端可访问（证书服务或 svg2gif 服务）。
- 环境准备：配置 `CHATTOOL_CERT_TOKEN` 与 `CHATTOOL_SVG2GIF_SERVER`（或通过参数传入）。
- 回滚：删除下载证书文件与输出文件。

## 用例 1：cert 列表

- 初始环境准备：
  - 服务端可访问。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool client cert list`，预期输出证书列表或空列表提示。

参考执行脚本（伪代码）：

```sh
chattool client cert list --server http://127.0.0.1:8000
```

## 用例 2：cert 申请与下载

- 初始环境准备：
  - 准备可用域名与 DNS 凭证。
- 相关文件：
  - `<output_dir>/<domain>/cert.pem`

预期过程和结果：
  1. 执行 `chattool client cert apply -d example.com -e user@example.com`，预期返回申请已提交。
  2. 执行 `chattool client cert download example.com -o <output_dir>`，预期下载证书文件。

参考执行脚本（伪代码）：

```sh
chattool client cert apply -d example.com -e user@example.com
chattool client cert download example.com -o /tmp/certs
```

## 用例 3：svg2gif 转换

- 初始环境准备：
  - 启动 `chattool serve svg2gif` 服务或可用远端服务。
  - 准备可用的 SVG 文件。
- 相关文件：
  - `<tmp>/demo.svg`
  - `<tmp>/demo.gif`

预期过程和结果：
  1. 执行 `chattool client svg2gif --svg <path> --gif <path>`，预期输出 GIF 路径与帧信息。

参考执行脚本（伪代码）：

```sh
chattool client svg2gif --svg /tmp/demo.svg --gif /tmp/demo.gif
```

## 清理 / 回滚

- 删除下载目录 `/tmp/certs/<domain>`。
