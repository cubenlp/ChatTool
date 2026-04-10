# test_chattool_env_basic

测试 `chattool env` 的基础链路，覆盖按类型拆分后的查看、列表、新建、保存、切换与删除配置。

## 元信息

- 命令：`chattool env <command> [args]`
- 目的：验证环境配置的读取与 profile 管理流程。
- 标签：`cli`
- 前置条件：无
- 环境准备：使用临时目录作为真实配置根目录（设置 `CHATTOOL_CONFIG_DIR`），并在真实文件系统中创建 `envs/<Config>/`。
- 回滚：测试结束后临时目录自动删除。

## 用例 1：查看当前配置（cat）

- 初始环境准备：
  - 创建临时目录作为环境配置根目录。
  - 创建 `envs/Feishu/.env`，包含普通键与敏感键。
- 相关文件：
  - `<tmp>/config/envs/Feishu/.env`

预期过程和结果：
  1. 执行 `chattool env cat -t feishu`，预期输出包含普通键，敏感键已按规则脱敏。
  2. 执行 `chattool env cat -t feishu --no-mask`，预期输出包含完整敏感键值。

参考执行脚本（伪代码）：

```sh
chattool env cat -t feishu
chattool env cat -t feishu --no-mask
```

## 用例 2：列出可用 profile（list）

- 初始环境准备：
  - 在 `<tmp>/config/envs/Feishu/` 下创建多个 `*.env` profile 文件。
- 相关文件：
  - `<tmp>/config/envs/Feishu/profile1.env`
  - `<tmp>/config/envs/Feishu/profile2.env`

预期过程和结果：
  1. 执行 `chattool env list -t feishu`，预期输出包含 `profile1.env` 与 `profile2.env`。

参考执行脚本（伪代码）：

```sh
chattool env list -t feishu
```

## 用例 3：保存 / 新建 / 切换 / 删除 profile

- 初始环境准备：
  - 通过 `chattool env set` 写入当前 `OpenAI` 与 `Feishu` 的活动配置。
- 相关文件：
  - `<tmp>/config/envs/OpenAI/.env`
  - `<tmp>/config/envs/OpenAI/work.env`
  - `<tmp>/config/envs/Feishu/.env`
  - `<tmp>/config/envs/Feishu/mini.env`

预期过程和结果：
  1. 执行 `chattool env save work -t openai`，预期生成 `envs/OpenAI/work.env`，内容包含当前 `OPENAI_API_KEY`。
  2. 执行 `chattool env new mini -t feishu`，预期创建 `envs/Feishu/mini.env`，但不修改 `envs/Feishu/.env`。
  3. 在交互终端里执行 `chattool env new -t openai`，预期先询问 profile 名，再继续补齐 `OpenAI` 字段，而不是直接退化成 `save`；完成后也不自动激活。
  4. 修改当前 `envs/OpenAI/.env` 内容后，执行 `chattool env use work -t openai`，预期提示已激活，并恢复为保存内容。
  5. 执行 `chattool env delete work -t openai`，预期 `work.env` 被删除。

参考执行脚本（伪代码）：

```sh
chattool env set OPENAI_API_KEY=sk-one
chattool env save work -t openai
chattool env set FEISHU_APP_ID=cli-one
chattool env set FEISHU_APP_SECRET=secret-one
chattool env new mini -t feishu
chattool env new -t openai
chattool env set OPENAI_API_KEY=sk-two
chattool env use work -t openai
chattool env delete work -t openai
```

## 用例 4：初始化指定配置类型（init -t）

- 初始环境准备：
  - 使用真实 `Feishu` 配置类型，不引入额外 mock 配置。
- 相关文件：
  - `<tmp>/config/envs/Feishu/.env`

预期过程和结果：
  1. 执行 `chattool env init -i -t feishu` 并输入新值，预期 `envs/Feishu/.env` 被更新。
  2. 执行 `chattool env init -t NonExistent`，预期输出提示未匹配配置类型。

参考执行脚本（伪代码）：

```sh
chattool env init -i -t feishu
chattool env init -t NonExistent
```

## 用例 5：set/get/unset 基础链路

- 初始环境准备：
  - 使用真实 `Feishu` 配置项进行写入和读取。
- 相关文件：
  - `<tmp>/config/envs/Feishu/.env`

预期过程和结果：
  1. 执行 `chattool env set FEISHU_DEFAULT_CHAT_ID=...`，预期写入 `envs/Feishu/.env`。
  2. 执行 `chattool env get FEISHU_DEFAULT_CHAT_ID`，预期输出对应值。
  3. 执行 `chattool env unset FEISHU_DEFAULT_CHAT_ID`，预期清空该键。

参考执行脚本（伪代码）：

```sh
chattool env set FEISHU_DEFAULT_CHAT_ID=oc_123
chattool env get FEISHU_DEFAULT_CHAT_ID
chattool env unset FEISHU_DEFAULT_CHAT_ID
```

## 清理 / 回滚

- 由临时目录自动回收，无需额外操作。
