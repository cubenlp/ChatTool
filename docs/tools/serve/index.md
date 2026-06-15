# Serve 本地服务

`chattool serve` 收纳本地服务类命令，包括截图服务、证书服务、飞书 webhook 服务、SVG 转 GIF 服务，以及轻量静态 HTML 服务。

## 本地 HTML 静态服务

`chattool serve local` 用 Python 标准库启动一个静态 HTTP 服务，用于快速打开本地 HTML 文件或目录。

打开当前目录下的 HTML 文件：

```bash
chattool serve local ./cli-tree.html --host 127.0.0.1 --port 8765
```

命令会服务该文件所在目录，并打开：

```text
http://127.0.0.1:8765/cli-tree.html
```

打开目录中的默认 `index.html`：

```bash
chattool serve local ./site --port 8765
```

打开目录中的指定 HTML：

```bash
chattool serve local ./reports --html cli-tree.html --port 8765
```

只查看解析结果，不启动服务：

```bash
chattool serve local ./cli-tree.html --dry-run
```

## 交互行为

`local` 遵循 ChatTool CLI 交互规范：

- 省略 `TARGET` 时默认使用当前目录 `.`。
- `-i` 会进入统一交互流程，提示填写 HTML 文件或目录，默认值为 `.`。
- `-I` 禁用交互，并使用默认当前目录。

## 其他服务

查看完整服务列表：

```bash
chattool serve --help
```
