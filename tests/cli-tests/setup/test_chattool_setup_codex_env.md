# test_chattool_setup_codex_env

测试 `chattool setup codex -e ...` 对 OpenAI 配置的读取顺序，聚焦配置解析层，不覆盖 npm 安装链路。

## 元信息

- 命令：`chattool setup codex -e <env>`
- 目的：验证 `setup codex` 可显式复用 `OpenAI` 配置，并遵守 `显式 env > 当前 oai 配置 > codex 现有配置` 的回退关系。
- 标签：`cli`
- 前置条件：无
- 环境准备：使用临时目录作为 `CHATTOOL_CONFIG_DIR`，在真实文件系统中构造 `envs/OpenAI/`。
- 回滚：测试结束后临时目录自动删除。

## 用例 1：profile 优先于保存配置，保存配置优先于环境变量

- 初始环境准备：
  - 创建 `envs/OpenAI/.env`
  - 创建 `envs/OpenAI/work.env`
  - 设置进程环境变量 `OPENAI_API_*`

预期过程和结果：
  1. 显式读取 `work` profile 时，若 profile 中存在某个字段，预期它优先于保存的 active OpenAI 配置。
  2. 若 profile 未提供某个字段，预期回退到保存的 `envs/OpenAI/.env`。
  3. 只有当保存配置也未提供某个字段时，才允许继续回退到进程环境变量。

参考执行脚本（伪代码）：

```sh
python -c 'from chattool.setup.codex import _load_openai_values_from_env_ref; import json; print(json.dumps(_load_openai_values_from_env_ref("work")))' 
```

## 用例 2：默认优先读取保存配置，再回退到环境变量

- 初始环境准备：
  - 创建 `envs/OpenAI/.env`
  - 设置不同的进程环境变量 `OPENAI_API_*`

预期过程和结果：
  1. 默认读取 `setup codex` 的基础 OpenAI 配置时，预期优先采用保存的 `envs/OpenAI/.env`。
  2. 若保存配置缺失某个字段，预期该字段才回退到进程环境变量。
  3. 这条规则属于 `setup` 开发规范：默认值来源必须先读保存配置，再读环境变量；只有显式 `-e/--env` 时，显式 env 才位于最前。

参考执行脚本（伪代码）：

```sh
python -c 'from chattool.setup.codex import _load_saved_openai_values; import json; print(json.dumps(_load_saved_openai_values()))'
```
