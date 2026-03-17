# CLI Tests（文档先行）

`cli-tests/` 是 CLI 测试设计入口，采用文档先行：先写 `.md`，再实现 `.py`。

## 目录结构

```
cli-tests/
├── index.md                 # 总览与规则说明
├── README.md                # 迁移计划
├── chatenv/
│   ├── test_chatenv_basic.md   # 文档先行：env 基础链路
│   └── test_chatenv_basic.py   # 对应 CLI 测试实现
├── mcp/
│   └── test_chattool_mcp_basic.md  # 文档先行：mcp 基础链路
├── zulip/
│   ├── test_chattool_zulip_news_basic.md   # 文档先行：zulip news
│   └── test_chattool_zulip_client_basic.md # 文档先行：zulip 客户端
└── setup/
    ├── test_chattool_setup_alias_basic.md      # alias 基础链路文档
    ├── test_chattool_setup_cli_basic.md        # setup 命令组基础链路文档
    ├── test_chattool_setup_alias_basic.py      # 对应 CLI 测试实现
    └── test_chattool_setup_interactive_policy_basic.md  # 交互策略文档
```

## 文件级别说明

- `index.md`：规范与目录说明，先更新这里再扩展具体用例。
- `README.md`：迁移计划与阶段安排。
- `**/*.md`：文档先行用例，必要时仅保留文档待配置。
- `**/*.py`：与 `.md` 同名的 CLI 测试实现。

## 结构

- 命令目录下优先平铺（通过文件名区分 `basic/topic`），避免无必要的层级嵌套。
- 命名规范：
  - 至少一个基础文件：`test_<cli>_<command>_basic.md/.py`
  - 按主题扩展：`test_<cli>_<command>_<topic>.md/.py`
- 目录示例：
  - `cli-tests/chattool/dns/test_chattool_dns_basic.md`
  - `cli-tests/chattool/dns/test_chattool_dns_timeout.md`

## 模板

以 `sample.test.md` 为模板，每个用例包含：

- 初始环境准备
- 相关文件
- 预期过程和结果（步骤与预期合并）
- 参考执行脚本（伪代码）
- 清理 / 回滚

## 一致性规则

- 文档与测试必须一致。
- 行为变化先改文档并说明原因。
- 修改文件必须回滚（推荐 try/finally）。

## 迁移策略

- 现有 `tests/` 测试逐步迁移为 `cli-tests/`，以 CLI 真实链路为主。
- 缺少测试环境/变量的用例先保留 `.md`，待配置后再补 `.py`。
