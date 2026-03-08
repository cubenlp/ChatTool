# Docker 模板生成（chattool docker）

`chattool docker` 用于快速生成浏览器相关 Docker 模板文件。

## 1) 基本用法

支持的模板：

- `chromium`
- `playwright`
- `headless-chromedriver`

标准用法：

```bash
chattool docker <chromium|playwright|headless-chromedriver> <output_dir>
```

示例：

```bash
chattool docker chromium /path/to
chattool docker playwright /path/to
chattool docker headless-chromedriver /path/to
```

会在目标目录生成：

- `docker-compose.yaml`
- `<template>.env.example`

## 2) 交互规则

`--help` 文案如下：

```text
--interactive / --no-interactive, -i / -I
Auto prompt when required args are missing, -i forces interactive, -I disables it.
```

行为说明：

1. 默认模式（不传 `-i/-I`）：  
   当缺少必要参数时自动交互询问（需 TTY）。
2. `-i` 强制交互：  
   即使参数齐全也会进入交互。
3. `-I` 强制非交互：  
   禁用自动询问；缺参时直接报错并显示 Usage。

常见示例：

```bash
# 缺参自动交互
chattool docker
chattool docker chromium

# 强制交互
chattool docker chromium /path/to -i

# 强制非交互（缺参会失败）
chattool docker -I
```

## 3) 常用参数

```bash
# 覆盖 env 默认值
chattool docker chromium /path/to --set PORT=3100 --set BIND_IP=0.0.0.0

# 自定义输出文件名
chattool docker chromium /path/to --compose-name compose.yaml --env-name chromium.local.env.example
```
