# Nginx 配置生成

`chattool nginx` 用来生成常见的 Nginx 配置模板，重点面向下面几类高频场景：

- 基础 `proxy_pass` 转发
- 带 HTTPS 入口的转发
- WebSocket 转发
- 静态目录站点
- 重定向

这个命令主要服务于“先交互式填写，再拿到一份可继续修改的配置骨架”的工作流。

## 命令形式

```bash
chattool nginx [template] [output_file] [--set KEY=VALUE] [-i|-I]
```

## 常用方式

### 1. 先列出模板

```bash
chattool nginx --list
```

### 2. 直接按模板生成

```bash
chattool nginx proxy-pass \
  --set SERVER_NAME=app.example.com \
  --set PROXY_PASS=http://127.0.0.1:8080
```

### 3. 交互式填写

```bash
chattool nginx -i
```

交互模式下会：

- 先选择配置大类
- 再选择模板
- 再只填写当前模板的必要参数
- 最后可选择直接输出到终端，或者写入 `.conf` 文件

## 模板列表

### `proxy-pass`

- 通用 HTTP 反向代理。
- 适合最常见的 `location / { proxy_pass ...; }` 场景。

### `proxy-pass-https`

- 适合常见的 `80 -> 443` 跳转 + HTTPS 反向代理。
- 默认生成一个跳转块和一个 HTTPS 转发块。

### `websocket-proxy`

- 通用 WebSocket 反代。
- 自动带 `Upgrade` / `Connection` / `proxy_http_version 1.1`。

### `static-root`

- 适合直接暴露静态目录或 NAS 目录。
- 默认带 `autoindex on;`。

### `redirect`

- 适合 80 端口跳转或其他简单重定向。
- 默认目标是 `https://$host$request_uri`。

## 主要变量

所有模板都通过 `--set KEY=VALUE` 覆盖变量。最常见变量包括：

- `SERVER_NAME`
- `LISTEN`
- `PROXY_PASS`
- `SSL_CERTIFICATE`
- `SSL_CERTIFICATE_KEY`
- `ROOT_DIR`
- `TARGET`

示例：

```bash
chattool nginx proxy-pass-https ./app.conf \
  --set SERVER_NAME=app.example.com \
  --set PROXY_PASS=http://127.0.0.1:8080 \
  --set SSL_CERTIFICATE=/etc/letsencrypt/live/app/fullchain.pem \
  --set SSL_CERTIFICATE_KEY=/etc/letsencrypt/live/app/privkey.pem
```

## 模板来源

当前模板来自仓库已有文档和 `reference/sites-available/` 目录里的真实配置，并按“配置形态”归纳成最常用的一小组模板。
