# SVG 转 GIF

通过 `chattool serve svg2gif` 启动本地服务，连接 Chromedriver 将 SVG 动画转换为 GIF。

## 前置条件

- 已安装 Chrome/Chromium 与 chromedriver
- chromedriver 服务已启动（远程 WebDriver）

示例启动 chromedriver：

```bash
chromedriver --port 9515
```

## 启动服务

```bash
chattool serve svg2gif --chromedriver-url http://127.0.0.1:9515
```

环境变量也可用：

```bash
export CHATTOOL_CHROMEDRIVER_URL=http://127.0.0.1:9515
chattool serve svg2gif
```

## 客户端调用

```bash
chattool client svg2gif --svg playground/termcap.svg --gif playground/termcap.gif
```

指定帧率：

```bash
chattool client svg2gif --svg playground/termcap.svg --fps 12
```

## 接口说明

服务端提供 `POST /svg2gif`，请求体示例：

```json
{
  "svg_path": "playground/termcap.svg",
  "gif_path": "playground/termcap.gif",
  "fps": 12
}
```

响应示例：

```json
{
  "ok": true,
  "gif_path": "/abs/path/playground/termcap.gif",
  "frames": 100,
  "duration_ms": 8347
}
```

## 常见问题

- `chromedriver_url is not configured`：未设置 chromedriver 地址，使用 `--chromedriver-url` 或 `CHATTOOL_CHROMEDRIVER_URL`。
- `SVG does not contain #screen_view`：SVG 不含 termcap/termtosvg 的动画节点，无法逐帧冻结。
