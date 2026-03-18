# test_chattool_tplogin_basic

测试 `chattool tplogin` 的基础链路，覆盖 info 与 ufw 子命令。

## 元信息

- 命令：`chattool tplogin <command> [args]`
- 目的：验证 TP-Link 路由器 CLI 的基础可用性。
- 标签：`cli`
- 前置条件：路由器可访问且凭证可用。
- 环境准备：配置路由器地址与账号密码。
- 回滚：删除新增的虚拟服务器规则。

## 用例 1：设备信息

- 初始环境准备：
  - 路由器可访问。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool tplogin info`，预期输出设备信息 JSON。

参考执行脚本（伪代码）：

```sh
chattool tplogin info
```

## 用例 2：ufw 状态

- 初始环境准备：
  - 路由器可访问。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool tplogin ufw status`，预期输出规则表。

参考执行脚本（伪代码）：

```sh
chattool tplogin ufw status
```

## 用例 3：ufw 添加与导出

- 初始环境准备：
  - 准备规则参数与输出文件路径。
- 相关文件：
  - `<tmp>/tplogin_ufw_rules.json`

预期过程和结果：
  1. 执行 `chattool tplogin ufw add 8080:192.168.1.2:80`，预期规则新增。
  2. 执行 `chattool tplogin ufw dump <path>`，预期生成规则文件。

参考执行脚本（伪代码）：

```sh
chattool tplogin ufw add 8080:192.168.1.2:80
chattool tplogin ufw dump /tmp/tplogin_ufw_rules.json
chattool tplogin ufw load /tmp/tplogin_ufw_rules.json --merge
```

## 用例 4：ufw 删除

- 初始环境准备：
  - 先创建至少一条规则。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool tplogin ufw delete --id 1`，预期规则删除成功并刷新列表。

参考执行脚本（伪代码）：

```sh
chattool tplogin ufw delete --id 1
```

## 清理 / 回滚

- 删除新增规则与导出文件。
