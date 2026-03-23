# CLI Tests（文档先行）

`cli-tests/` 是 ChatTool 仓库内唯一长期维护的测试设计入口，采用文档先行：先写 `.md`，再实现 `.py`。

## 目录结构

当前结构。

```
cli-tests/
├── index.md                 # 总览与规则说明
├── README.md                # 迁移计划与执行顺序
├── browser/
│   └── test_chattool_browser_basic.md
├── client/
│   └── test_chattool_client_basic.md
├── dns/
│   └── test_chattool_dns_basic.md
├── docker/
│   └── test_chattool_docker_basic.md
├── env/
│   └── test_chattool_env_basic.md
├── explore/
│   └── test_chattool_explore_basic.md
├── gh/
│   └── test_chattool_gh_basic.md
├── image/
│   └── test_chattool_image_basic.md
├── lark/
│   └── test_chattool_lark_basic.md
├── mcp/
│   └── test_chattool_mcp_basic.md
├── network/
│   └── test_chattool_network_basic.md
├── serve/
│   └── test_chattool_serve_basic.md
├── setup/
│   └── test_chattool_setup_basic.md
├── skill/
│   └── test_chattool_skill_basic.md
├── tplogin/
│   └── test_chattool_tplogin_basic.md
└── zulip/
    └── test_chattool_zulip_basic.md
```

## 文件级别说明

- `index.md`：规范与目录说明，先更新这里再扩展具体用例。
- `README.md`：CLI 测试长期规则。
- `**/*.md`：文档先行用例，是评审与验收的主对象。
- `**/*.py`：与 `.md` 同名的真实 CLI 测试实现。

## 命名规范

- 至少一个基础文件：`test_<cli>_<command>_basic.md/.py`
- 按主题扩展：`test_<cli>_<command>_<topic>.md/.py`
- 命名必须与 CLI 命令保持一致。

## 文档结构

- 每个 case 采用“初始环境准备 / 预期过程和结果 / 参考执行脚本（伪代码）”。
- `预期过程和结果` 的每一步包含“执行动作 + 紧接着预期”。
- 每个 case 最后必须有 `sh` 伪代码。
- 涉及文件改写的用例必须包含回滚说明。

## 模板

- 以 `cli-tests/env/test_chattool_env_basic.md` 为模板。

## 仓库规则

- ChatTool 仓库后续只长期维护 `cli-tests/` 这条测试主线。
- `tests/` 为弃用区，仅保留历史参考，不再作为新开发默认测试落点。
- 新 CLI 行为必须先补 `.md`，没有对应 `.md` 的 `.py` 不应新增。
- 缺少真实环境/变量的用例先保留 `.md`，待环境满足后再补 `.py`。
