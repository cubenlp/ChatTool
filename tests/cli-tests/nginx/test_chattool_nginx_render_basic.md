# test_chattool_nginx_render_basic

测试 `chattool nginx` 的真实基础链路，覆盖通用反代、WebSocket 转发、静态目录模板与文件输出。

## 元信息

- 命令：`chattool nginx [template] [output_file] [--set KEY=VALUE]`
- 目的：验证 Nginx 配置模板可直接从真实 CLI 产出。
- 标签：`cli`
- 前置条件：无第三方服务依赖。
- 环境准备：准备临时输出目录。
- 回滚：删除生成的配置文件。

## 用例 1：stdout 输出通用 HTTP 反代模板

- 初始环境准备：
  - 无
- 相关文件：
  - 无

预期过程和结果：
1. 执行 `chattool nginx proxy-pass --set SERVER_NAME=app.example.com --set PROXY_PASS=http://127.0.0.1:8080`，预期 stdout 包含 `server_name app.example.com;` 与 `proxy_pass http://127.0.0.1:8080;`。

参考执行脚本（伪代码）：

```sh
chattool nginx proxy-pass --set SERVER_NAME=app.example.com --set PROXY_PASS=http://127.0.0.1:8080
```

## 用例 2：写入 WebSocket 转发模板文件

- 初始环境准备：
  - 准备临时目录。
- 相关文件：
  - `<tmp>/websocket.conf`

预期过程和结果：
1. 执行 `chattool nginx websocket-proxy <tmp>/websocket.conf --set SERVER_NAME=ws.example.com --set PROXY_PASS=http://127.0.0.1:3000 --force`，预期输出文件被创建。
2. 预期文件中包含 `proxy_http_version 1.1;`、`proxy_set_header Upgrade $http_upgrade;` 和 `proxy_set_header Connection "upgrade";`。

参考执行脚本（伪代码）：

```sh
chattool nginx websocket-proxy /tmp/websocket.conf --set SERVER_NAME=ws.example.com --set PROXY_PASS=http://127.0.0.1:3000 --force
```

## 用例 3：写入静态目录模板文件

- 初始环境准备：
  - 准备临时目录。
- 相关文件：
  - `<tmp>/nas.conf`

预期过程和结果：
1. 执行 `chattool nginx static-root <tmp>/nas.conf --set SERVER_NAME=share.example.com --set ROOT_DIR=/var/www/example-site --force`，预期输出文件被创建。
2. 预期文件中包含 `root /var/www/example-site;`、`autoindex on;` 和 `charset utf-8;`。

参考执行脚本（伪代码）：

```sh
chattool nginx static-root /tmp/nas.conf --set SERVER_NAME=share.example.com --set ROOT_DIR=/var/www/example-site --force
```

## 用例 4：生成 HTTP 到 HTTPS 跳转模板

- 初始环境准备：
  - 无
- 相关文件：
  - 无

预期过程和结果：
1. 执行 `chattool nginx redirect --set SERVER_NAME="example.com www.example.com"`，预期 stdout 中包含 `return 301 https://$host$request_uri;`。

参考执行脚本（伪代码）：

```sh
chattool nginx redirect --set SERVER_NAME="example.com www.example.com"
```

## 清理 / 回滚

- 删除生成的配置文件。
