# test_chattool_client_interactive_basic

测试 `chattool client` 子命令接入共享交互 schema/resolver 之后的 mock CLI 行为。

## 元信息

- 命令：`chattool client cert ...`、`chattool client svg2gif ...`
- 目的：验证 client 子命令缺参时默认补问，`-I` 才禁用交互并直接报错。
- 标签：`cli`、`mock`
- 前置条件：无真实远端服务依赖；通过 monkeypatch / mock 隔离交互与 requests。
- 环境准备：使用 `CliRunner` 调用统一入口 `chattool`。
- 回滚：无。

## 用例 1：`svg2gif` 缺少 `--svg` 时自动补问

预期过程和结果：
1. 在交互可用环境下执行 `chattool client svg2gif`。
2. 预期自动补问 `SVG 文件路径`，然后调用远端接口。

## 用例 2：`svg2gif -I` 禁用交互后直接报错

预期过程和结果：
1. 执行 `chattool client svg2gif -I`。
2. 预期不补问，直接报缺少必要参数。

## 用例 3：`cert apply` 缺参时自动补问关键字段

预期过程和结果：
1. 在交互可用环境下执行 `chattool client cert apply`。
2. 预期至少补问 `域名` 和 `Let's Encrypt 邮箱`，随后发起申请请求。

## 用例 4：`cert download` 缺少 domain 时自动补问

预期过程和结果：
1. 在交互可用环境下执行 `chattool client cert download`。
2. 预期补问证书域名，再继续下载流程。

## 清理 / 回滚

- 无需额外操作。
