# Docker 模板生成与环境检查

## `chattool setup docker`

`chattool setup docker` 用于检查本机 Docker / Docker Compose / docker 组状态。

默认模式下只打印建议命令，不直接执行 `sudo`。

```bash
chattool setup docker
```

如果你希望在交互确认后直接执行建议的 `sudo` 命令，需要显式传入 `--sudo`：

```bash
chattool setup docker --sudo -i
```

当前命令不会自动修改共享目录权限或所有权；这类权限操作需要用户自行管理。

---

# `chattool docker` 模板生成

`chattool docker` 用于快速生成浏览器相关 Docker 模板文件。

仓库根目录另外提供了一个静态的 `Dockerfile.playground`，用于直接构建一个 ChatTool workspace 启动镜像，不经过 `chattool docker` 模板生成。

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

## 4) Workspace 镜像

直接构建：

```bash
docker build -f Dockerfile.playground -t chattool-playground .
```

镜像启动后会按固定顺序执行：

1. `chattool setup workspace /workspace --with-chattool --chattool-source /playground/ChatTool -I`
2. `chattool env set CHATTOOL_SKILLS_DIR=/workspace/skills`
3. `chattool setup alias`

镜像构建阶段会先在 `/opt/venv` 虚拟环境中安装 ChatTool，然后启动 `sshd`。默认工作目录是 `/workspace`。
