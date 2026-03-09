# Chrome 环境配置

`chattool` 提供了便捷的工具来管理 Chrome 和 Chromedriver 环境，支持自动化安装和快速启动服务。

## 1. 安装 Chrome 和 Chromedriver

`chattool` 可以自动检测当前系统安装的 Google Chrome 版本，并下载匹配的 Chromedriver。

### 基本用法

```bash
# 自动检测版本并下载 Chromedriver
chattool setup chrome
```

该命令会执行以下操作：
1. 检测系统中已安装的 Google Chrome 版本。
2. 从官方源获取对应版本的 Chromedriver 下载链接。
3. 下载并解压 Chromedriver 到默认目录（通常是 `~/.local/bin`）。
4. 设置可执行权限并校验 `chromedriver --version`。

如果未安装 Google Chrome，会打印安装提示（`.deb + sudo apt install`）。

### 交互模式

如果你希望自定义安装路径或确认每一步操作，可以使用交互模式：

```bash
chattool setup chrome -i
# 或
chattool setup chrome --interactive
```

## 2. 启动服务

`chattool` 提供统一命令来启动 Chrome 浏览器（CDP）或 Chromedriver 服务。

### 启动 Chromedriver

启动 WebDriver 服务，供 Selenium 等工具连接。

```bash
# 默认就是 driver 模式（默认端口 9515）
chattool serve chrome

# 指定端口
chattool serve chrome --driver --port 9515

# 允许外部连接（注意安全风险）
chattool serve chrome --driver --allowed-ips 0.0.0.0
```

### 启动 Chrome (CDP 模式)

启动带有远程调试端口的 Chrome 浏览器，供 CDP (Chrome DevTools Protocol) 客户端连接。

```bash
# 在默认端口 9222 启动远程调试
chattool serve chrome --cdp

# Linux 无 DISPLAY 时会自动启用 headless
chattool serve chrome --cdp

# 指定用户数据目录（避免污染默认配置）
chattool serve chrome --cdp --user-data-dir /tmp/my-chrome-profile

# 服务器上常用（无沙箱）
chattool serve chrome --cdp --no-sandbox

# 允许外部网络访问 CDP（注意安全）
chattool serve chrome --cdp --bind-address 0.0.0.0
```

### 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--driver` | `False` | 显式启动 Chromedriver 服务（默认模式） |
| `--cdp` | `False` | 启动 Google Chrome (Remote Debugging) |
| `--port` | `driver=9515 / cdp=9222` | 监听端口 |
| `--allowed-ips` | `127.0.0.1` | 允许连接的 IP 列表 (仅 Driver 模式有效) |
| `--user-data-dir` | `/tmp/chrome-profile` | Chrome 用户数据目录 (仅 CDP 模式有效) |
| `--headless` | `False` | 启用无头模式 (仅 CDP 模式有效) |
| `--bind-address` | `127.0.0.1` | CDP 监听地址 (仅 CDP 模式有效) |
| `--no-sandbox` | `False` | 以 `--no-sandbox` 启动 Chrome（服务器场景常用） |

!!! warning "互斥选项"
    `--driver` 和 `--cdp` 是互斥的，每次只能启动其中一种模式。
