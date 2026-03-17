# SVG 转 GIF

通过 `chattool serve svg2gif` 启动本地服务，连接 Chromedriver 将 SVG 动画转换为 GIF。服务会按 SVG 关键帧冻结动画并裁剪到 `#terminal` 区域，避免两侧边框。

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

指定帧率（仅在 SVG 没有关键帧定义时生效）：

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

## 渲染说明

- GIF 默认 **无限循环**（loop=0）。
- 若 SVG 含 `@keyframes roll` 的百分比关键帧，服务会按关键帧时间采样，避免画面波动。
- 截图以 `#terminal` 的 `getBoundingClientRect()` 裁剪，确保输出尺寸与 SVG 画面一致。

## 常见问题

- `chromedriver_url is not configured`：未设置 chromedriver 地址，使用 `--chromedriver-url` 或 `CHATTOOL_CHROMEDRIVER_URL`。
- `SVG does not contain #screen_view`：SVG 不含 termcap/termtosvg 的动画节点，无法逐帧冻结。
- 画面有边框或错位：请确认 SVG 根节点为 `id="terminal"` 且包含 `id="screen"` 与 `id="screen_view"`。
