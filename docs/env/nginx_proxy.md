# Nginx 反向代理配置

在生产环境中，直接暴露 Chrome 远程调试端口 (CDP) 或 WebDriver 端口是不安全的。推荐使用 Nginx 进行反向代理，并配置适当的访问控制。

如果你想先快速得到一个可编辑模板，可以直接使用：

```bash
chattool nginx --list
chattool nginx proxy-pass --set SERVER_NAME=app.example.com --set PROXY_PASS=http://127.0.0.1:8080
chattool nginx websocket-proxy ./websocket.conf --set SERVER_NAME=ws.example.com --set PROXY_PASS=http://127.0.0.1:3000
chattool nginx -i
```

`chattool nginx` 当前会把常见场景整理成模板，并支持交互式逐项填写；下面这份文档继续保留原理说明和手写示例。

## 1. WebDriver (HTTP) 代理

WebDriver (如 Chromedriver) 主要使用 HTTP 协议进行通信。以下配置示例展示了如何代理 WebDriver 请求。

假设 Chromedriver 运行在本地 `127.0.0.1:9515`（可通过 `chattool serve chrome --driver --port 9515` 启动）。

```nginx
server {
    listen 80;
    server_name webdriver.example.com;

    location / {
        proxy_pass http://127.0.0.1:9515;
        
        # 基本代理头设置
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 增加超时时间，防止长轮询中断
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        
        # 限制访问来源 (可选)
        allow 192.168.1.0/24;
        deny all;
    }
}
```

## 2. CDP (WebSocket) 代理

Chrome DevTools Protocol (CDP) 依赖 WebSocket 进行双向通信，同时也提供了一些 HTTP 接口（如 `/json/list` 用于获取调试目标列表）。

假设 Chrome 远程调试端口开启在 `127.0.0.1:9222`（可通过 `chattool serve chrome --cdp --port 9222` 启动）。

```nginx
server {
    listen 80;
    server_name cdp.example.com;

    location / {
        proxy_pass http://127.0.0.1:9222;

        # 启用 WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 必须设置 Host 头，否则 Chrome 可能拒绝连接
        proxy_set_header Host localhost; 
        # 注意: Chrome 默认只允许 localhost 或 127.0.0.1 的 Host 头
        # 如果 Nginx 和 Chrome 在同一台机器，建议设置为 localhost
        
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400s; # WebSocket 长连接超时
    }
}
```

!!! tip "Host 头的重要性"
    Chrome 出于安全考虑，默认会检查 Host 头。如果 Nginx 传递了外部域名作为 Host，Chrome 可能会拒绝连接（返回 `Host header is specified and is not an IP address or localhost.`）。
    因此，`proxy_set_header Host localhost;` 是关键配置。

## 3. 路径前缀代理 (高级)

如果你想在同一个域名下通过不同路径代理多个服务，可以使用 `location` 匹配。

```nginx
server {
    listen 80;
    server_name tools.example.com;

    # WebDriver 代理
    location /webdriver/ {
        # 注意末尾的斜杠，去除前缀
        proxy_pass http://127.0.0.1:9515/; 
        
        proxy_set_header Host $host;
        proxy_read_timeout 300s;
    }

    # CDP 代理
    location /cdp/ {
        proxy_pass http://127.0.0.1:9222/;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host localhost;
    }
}
```

!!! warning "路径重写注意事项"
    使用路径前缀代理时，需确保后端服务能够处理路径剥离（Rewrite）。对于 CDP，WebSocket 连接地址通常是绝对路径（如 `/devtools/browser/...`），通过路径前缀代理可能会导致客户端无法正确解析 WebSocket URL。
    **推荐使用子域名（如 `cdp.example.com`）而非子路径（如 `example.com/cdp/`）来代理 CDP 服务。**

## 4. 安全建议

### Basic Auth 认证

为防止未授权访问，建议在 Nginx 层面添加 Basic Auth。

1. 生成密码文件：
   ```bash
   htpasswd -c /etc/nginx/.htpasswd user1
   ```

2. 在 Nginx 配置中启用：
   ```nginx
   location / {
       auth_basic "Restricted Access";
       auth_basic_user_file /etc/nginx/.htpasswd;
       
       proxy_pass http://127.0.0.1:9222;
       # ... 其他配置
   }
   ```

注意：部分自动化工具（如 Selenium 或 Puppeteer）可能不支持直接在 URL 中携带认证信息，或者需要特殊配置才能通过 Nginx 的 Basic Auth。
