# test_chattool_setup_codex_env

测试 `chattool setup codex -e ...` 对 OpenAI 配置的读取顺序，聚焦配置解析层，不覆盖 npm 安装链路。

## 元信息

- 命令：`chattool setup codex -e <env>`
- 目的：验证 `setup codex` 可显式复用 `OpenAI` 配置，并遵守 `显式 env > 当前 oai 配置 > codex 现有配置` 的回退关系。
- 标签：`cli`
- 前置条件：无
- 环境准备：使用临时目录作为 `CHATTOOL_CONFIG_DIR`，在真实文件系统中构造 `envs/OpenAI/`。
- 回滚：测试结束后临时目录自动删除。

## 用例 1：profile 优先于当前 oai，当前 oai 优先于类型默认 `.env`

- 初始环境准备：
  - 创建 `envs/OpenAI/.env`
  - 创建 `envs/OpenAI/work.env`
  - 设置进程环境变量 `OPENAI_API_*`

预期过程和结果：
  1. 显式读取 `work` profile 时，若 profile 中存在某个字段，预期它优先于当前 `oai/openai` 生效配置。
  2. 若 profile 未提供某个字段，预期回退到当前 `oai/openai` 生效配置。
  3. 若当前 `oai/openai` 生效配置也未提供，预期再回退到 `envs/OpenAI/.env`。

参考执行脚本（伪代码）：

```sh
python -c 'from chattool.setup.codex import _load_openai_values_from_env_ref; import json; print(json.dumps(_load_openai_values_from_env_ref("work")))' 
```
