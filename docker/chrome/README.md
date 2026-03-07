# 最简单浏览器服务（给 AI 用）

目标：只保留一个 Browserless 服务，AI 侧直接用一个 URL 即可发起浏览器操作。

## 1) 启动

在项目根目录执行：

```bash
docker compose -f /home/zhihong/workspace/ChatTool/docker/chrome/docker-compose.yml up -d
```

默认地址：

- HTTP: `http://127.0.0.1:3000`
- WebSocket: `ws://127.0.0.1:3000`

## 2) 可选：加 TOKEN（推荐）

临时方式：

```bash
TOKEN=my-secret-token docker-compose up -d
```

加 token 后，调用时在 URL 带上：

```text
?token=my-secret-token
```

## 3) 给 AI 集成建议

- 本机集成：直接用 `127.0.0.1:3000`。
- 远程部署：先走 Nginx 反代再开放，不要直接公网暴露 3000。
- 多用户场景：尽量每次任务新建会话，不复用持久 profile，避免 cookie 串号。

## 4) 停止

```bash
docker compose -f /home/zhihong/workspace/ChatTool/docker/chrome/docker-compose.yml down
```
