# test_chattool_browser_basic

测试 `chattool browser` 的基础链路，覆盖二维码登录的 CLI 调用与输出路径。

## 元信息

- 命令：`chattool browser <command> [args]`
- 目的：验证浏览器工具的核心命令可用。
- 标签：`cli`
- 前置条件：浏览器后端可用（playwright/selenium/chromium）。
- 环境准备：配置 `BROWSER_DEFAULT_BACKEND` 或通过 `--backend` 指定，必要时设置后端 URL。
- 回滚：删除输出二维码图片与调试目录。

## 用例 1：生成二维码（xhs-qrcode）

- 初始环境准备：
  - 确认默认后端可用或指定 `--backend`。
  - selenium 后端需设置 `BROWSER_SELENIUM_REMOTE_URL`；chromium 后端需设置 `BROWSER_CHROMIUM_CDP_URL`。
- 相关文件：
  - `<tmp>/xhs-qrcode.png`
  - `/tmp/chattool_xhs_debug/`（可选）

预期过程和结果：
  1. 执行 `chattool browser xhs-qrcode --output <path>`，预期生成二维码图片文件。
  2. 执行 `chattool browser xhs-qrcode --backend playwright`，预期使用指定后端。
  3. 执行 `chattool browser xhs-qrcode --debug --debug-dir <path>`，预期生成调试目录。

参考执行脚本（伪代码）：

```sh
chattool browser xhs-qrcode --output /tmp/xhs-qrcode.png
chattool browser xhs-qrcode --backend playwright
chattool browser xhs-qrcode --debug --debug-dir /tmp/chattool_xhs_debug
```

## 清理 / 回滚

- 删除输出图片与调试目录。
