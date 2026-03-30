# Mock CLI Tests（文档先行）

`mock-cli-tests/` 收纳 ChatTool 仓库内所有基于 mock 的 CLI 测试，采用文档先行：先写 `.md`，再实现 `.py`。

## 目录结构

当前结构。

```text
mock-cli-tests/
├── index.md
├── README.md
├── conftest.py
├── cc/
│   └── test_chattool_cc_basic.md
├── client/
│   └── test_chattool_client_dispatch_basic.md
├── dns/
│   └── test_chattool_dns_basic.md
├── explore/
│   └── test_chattool_explore_basic.md
└── gh/
    ├── test_chattool_gh_basic.md
    └── test_chattool_gh_actions_diagnostics.md
```

## 文件级别说明

- `index.md`：规范与目录说明。
- `README.md`：mock CLI 测试长期规则。
- `**/*.md`：mock CLI 用例设计文档，是评审与维护对象。
- `**/*.py`：与 `.md` 同名的 mock CLI 测试实现。

## 命名规范

- 至少一个基础文件：`test_<cli>_<command>_basic.md/.py`
- 按主题扩展：`test_<cli>_<command>_<topic>.md/.py`
- 命名必须与 CLI 命令保持一致。

## 使用边界

- `mock-cli-tests/` 用于验证 CLI 入口编排、参数流向、输出格式、懒加载和交互分支。
- `cli-tests/` 只保留真实 CLI 链路与真实环境验收。
- `tests/` 为历史参考区，不再作为新 mock CLI 测试的默认落点。
