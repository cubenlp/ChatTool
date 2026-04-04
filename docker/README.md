# Docker 模板

预置模板：

- `docker-compose.chromium.yml`
- `docker-compose.playwright.yml`
- `docker-compose.headless-chromedriver.yml`
- `docker-compose.nas.yml`
- `../Dockerfile.playground`
- `chromium.env.example`
- `playwright.env.example`
- `headless-chromedriver.env.example`
- `nas.env.example`

CLI 生成方式：

```bash
chattool docker chromium /path/to
chattool docker playwright /path/to
chattool docker headless-chromedriver /path/to
chattool docker nas /path/to
```

会在目标目录生成：

- `docker-compose.yaml`
- `<template>.env.example`

推荐将 env 拷贝成 `.env` 后再启动。

交互规则（与 `chattool docker --help` 一致）：

- `--interactive/--no-interactive`（`-i/-I`）
- 规则：`Auto prompt when required args are missing, -i forces interactive, -I disables it.`

具体行为：

1. 默认模式（不传 `-i/-I`）  
   缺少必要参数时自动进入交互询问（需有 TTY）。

```bash
chattool docker
chattool docker chromium
```

2. 参数齐全时默认不交互，直接生成文件。

```bash
chattool docker chromium /path/to
```

3. `-i` 强制交互  
   即使参数已给齐，也会进入交互，可重新选择模板和输出目录。

```bash
chattool docker chromium /path/to -i
```

4. `-I` 强制非交互  
   不允许自动询问；若缺参会直接报错并显示 Usage。

```bash
chattool docker -I
```

覆盖默认参数（更通用）：

```bash
chattool docker chromium /path/to --set PORT=3100 --set BIND_IP=0.0.0.0
chattool docker playwright /path/to --set VOLUME=/data/project --set COMMAND="npm test"
chattool docker headless-chromedriver /path/to --set WEBDRIVER_PORT=5555
chattool docker nas /path/to --set IMAGE=halverneus/static-file-server:latest --set RESOURCE_DIR=/path/to/resources --set PORT=9080 --set URL_PREFIX=/prefix
```

自定义文件名：

```bash
chattool docker chromium /path/to --compose-name compose.yaml --env-name chromium.local.env.example
```

另外，仓库根目录提供了一个直接可构建的 Playground 镜像文件：

```bash
docker build -f Dockerfile.playground -t chattool-playground .
```

这个镜像会在线性启动流程里依次执行：

1. `chattool setup playground`
2. `chattool env set CHATTOOL_SKILLS_DIR=/workspace/skills`
3. `chattool setup alias`

构建时会先在 `/opt/venv` 虚拟环境里安装 ChatTool，随后启动 `sshd`。
