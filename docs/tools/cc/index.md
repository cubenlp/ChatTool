# CC-Connect 管理

`chattool cc` 提供 cc-connect 的最小可用管理能力，面向快速上手（单配置、单项目）。

## 快速开始

```bash
chattool cc setup
chattool cc init -i
chattool cc start
```

默认配置文件：`~/.cc-connect/config.toml`
默认日志文件：`~/.cc-connect/cc-connect.log`

## 命令

- `chattool cc setup`：安装/检查 Node.js、npm 与 cc-connect
- `chattool cc init`：生成最小可用配置（Agent + Platform + Project）
- `chattool cc start`：启动 cc-connect（前台输出，同时写入日志）
- `chattool cc status`：查看基础状态
- `chattool cc logs`：查看/跟随日志
- `chattool cc doctor`：快速自检

## 说明

- 一阶段只覆盖高频最小能力，更多高级配置请直接编辑 `config.toml`。
- `chattool cc init -i` 会引导填写 Agent/Platform/Mode 及必要凭证，并在已有配置时作为默认值提示。
- 飞书平台会直接提示 `app_id` 与 `app_secret`。
