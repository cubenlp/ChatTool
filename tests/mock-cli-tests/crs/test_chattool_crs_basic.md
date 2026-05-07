# test_chattool_crs_basic

## 目标

验证 `chattool crs` 第一版只覆盖获取/查询相关能力，并遵守 ChatTool 的 lazy CLI、typed env、缺参交互和 mock CLI 测试约定。

## Case 1: 顶层 help 暴露命令组

### 初始环境准备

- 使用 `CliRunner` 调用统一入口 `chattool.client.main.cli`。

### 预期过程和结果

- 执行 `chattool crs --help`。
- 输出包含 `auth`、`stats`、`models`、`admin`。
- 执行 `chattool crs admin --help`。
- 输出包含 `dashboard`、`api-keys`、`accounts`。

### 参考执行脚本

```sh
chattool crs --help
chattool crs admin --help
```

## Case 2: stats 读取 CRS env 并调用 self stats

### 初始环境准备

- mock `CRSClient.user_stats` 返回 API key usage 与 OpenAI Codex usage。
- mock `CRSConfig` 运行时值，避免真实网络请求。

### 预期过程和结果

- 执行 `chattool crs stats`。
- CLI 使用 `CRS_API_BASE` 和 `CRS_API_KEY` 创建 client。
- 输出 API key 名称、请求数、token、cost、Codex primary/secondary 使用百分比和 reset 剩余时间。

### 参考执行脚本

```sh
chattool crs stats
```

## Case 3: models 传递 period

### 初始环境准备

- mock `CRSClient.user_model_stats` 记录 `period` 参数并返回模型统计。

### 预期过程和结果

- 执行 `chattool crs models --period daily`。
- CLI 调用模型统计接口时传入 `daily`。
- 输出模型名、请求数、token 和 cost。

### 参考执行脚本

```sh
chattool crs models --period daily
```

## Case 4: auth login --save 写入本地 CRS typed env

### 初始环境准备

- 使用临时 `CHATARCH_HOME` / `CHATARCH_ENV_DIR`。
- mock `CRSClient.login` 返回 token。

### 预期过程和结果

- 执行 `chattool crs auth login --api-base ... --username ... --password ... --save -I`。
- 命令成功，不打印明文 token。
- active CRS env 文件写入 `CRS_ACCESS_TOKEN`。

### 参考执行脚本

```sh
chattool crs auth login --api-base https://crs.example.com --username admin --password secret --save -I
```

## Case 5: admin 查询使用 Bearer token

### 初始环境准备

- mock `CRSConfig.CRS_ACCESS_TOKEN`。
- mock `CRSClient.dashboard` / `api_keys` / `accounts` 返回固定数据。

### 预期过程和结果

- 执行 `chattool crs admin dashboard`，输出 dashboard 概要。
- 执行 `chattool crs admin api-keys`，输出 API key 列表。
- 执行 `chattool crs admin accounts --type openai`，输出账户列表。
- 命令只调用读取类接口，不调用任何编辑/删除/刷新类方法。

### 参考执行脚本

```sh
chattool crs admin dashboard
chattool crs admin api-keys
chattool crs admin accounts --type openai
```

## Case 6: -I 缺参失败

### 初始环境准备

- 不设置登录所需参数。

### 预期过程和结果

- 执行 `chattool crs auth login -I`。
- 命令失败并提示缺少 `api_base`。

### 参考执行脚本

```sh
chattool crs auth login -I
```
