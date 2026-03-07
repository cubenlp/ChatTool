# TP-Link 路由器管理工具

ChatTool 提供了 TP-Link 路由器（基于 WDR5620 逆向）的管理工具，支持获取设备信息和管理虚拟服务器（端口转发）。

## 核心特性

- **自动登录**：支持密码加密与 stok 自动维护。
- **虚拟服务器管理**：提供 UFW 风格的命令行工具，轻松管理端口转发规则。
- **批量操作**：支持规则的导出（Dump）与导入（Load），方便迁移和备份。

## 快速开始

### 1. 配置凭证

在项目根目录或配置目录下的 `.env` 文件中设置路由器的地址和密码：

```bash
# TP-Link 路由器配置
TPLOGIN_URL="http://192.168.1.1"
TPLOGIN_AUTH_PASSWORD="your-router-password"
TPLOGIN_AUTH_KEY="your-router-auth-key"
TPLOGIN_AUTH_DICTIONARY="your-router-auth-dictionary"
```

其中 `TPLOGIN_AUTH_KEY` 与 `TPLOGIN_AUTH_DICTIONARY` 为路由器登录加密所需参数，未配置时无法登录。

### 2. 命令行工具 (CLI)

`chattool tplogin` 命令组提供了丰富的路由器管理功能。

#### 设备信息

获取路由器基本信息：

```bash
chattool tplogin info
```

#### 虚拟服务器 (UFW 风格)

使用 `chattool tplogin ufw` 命令管理端口转发规则。

**查看状态**

列出当前所有虚拟服务器规则：

```bash
chattool tplogin ufw status
# 或者简写
chattool tplogin ufw
```

**添加规则**

语法：`chattool tplogin ufw add RULE_SPEC [--proto PROTO]`

`RULE_SPEC` 格式为 `OUT_PORT:LOCAL_IP:IN_PORT`。支持端口段。

```bash
# 将外部 8080 端口转发到内部 192.168.1.100 的 80 端口
chattool tplogin ufw add 8080:192.168.1.100:80

# 指定协议 (默认为 all，可选 tcp, udp)
chattool tplogin ufw add 2222:192.168.1.100:22 --proto tcp

# 端口段转发 (外部 6000-6010 映射到内部起始 6000)
chattool tplogin ufw add 6000-6010:192.168.1.100:6000
```

**删除规则**

支持按 ID 或 名称删除：

```bash
# 按列表中的 ID 删除
chattool tplogin ufw delete --id 1

# 按规则名称删除
chattool tplogin ufw delete --name redirect_1
```

**批量导出与导入**

支持将规则导出为 JSON 文件，或从文件批量加载规则。

```bash
# 导出当前规则到文件
chattool tplogin ufw dump rules_backup.json

# 导入规则 (默认合并模式：跳过已存在的，添加新的)
chattool tplogin ufw load rules_backup.json

# 导入规则 (清理模式：删除多余的旧规则，保持与文件一致)
chattool tplogin ufw load rules_backup.json --delete

# 导入规则 (覆盖模式：清空现有所有规则，重新添加)
chattool tplogin ufw load rules_backup.json --replace
```

### 3. Python API 使用

你也可以在代码中直接使用 `TPLogin` 类进行操作。

```python
from chattool.tools import TPLogin

# 初始化 (会自动读取环境变量)
client = TPLogin()

# 手动指定参数
# client = TPLogin(
#     url="http://192.168.1.1",
#     password="xxx",
#     auth_key="xxx",
#     auth_dictionary="xxx"
# )

# 1. 获取设备信息
info = client.get_device_info()
print(info)

# 2. 获取虚拟服务器列表
rules = client.list_virtual_servers()
for rule in rules:
    print(f"{rule['name']}: {rule['src_dport_start']} -> {rule['dest_ip']}:{rule['dest_port']}")

# 3. 添加规则
client.add_virtual_server(
    src_port_start=8080,
    src_port_end=None, # 单个端口
    dest_ip="192.168.1.100",
    dest_port=80,
    proto="tcp"
)

# 4. 删除规则
client.delete_virtual_server("redirect_1")
```
