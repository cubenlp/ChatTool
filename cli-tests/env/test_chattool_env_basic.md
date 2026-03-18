# test_chattool_env_basic

测试 `chattool env` 的基础链路，覆盖查看、列表、保存、切换与删除配置。

## 元信息

- 命令：`chattool env <command> [args]`
- 目的：验证环境配置的读取与 profile 管理流程。
- 标签：`cli`
- 前置条件：无
- 环境准备：使用临时目录模拟环境配置目录与 `.env` 文件（设置 `CHATTOOL_CONFIG_DIR`）。
- 回滚：测试结束后临时目录自动删除。

## 用例 1：查看当前配置（cat）

- 初始环境准备：
  - 创建临时目录作为环境配置根目录。
  - 创建 `.env` 文件，包含普通键与敏感键。
- 相关文件：
  - `<tmp>/.env`
  - `<tmp>/envs/*.env`

预期过程和结果：
  1. 执行 `chattool env cat`，预期输出包含普通键，敏感键已按规则脱敏。
  2. 执行 `chattool env cat --no-mask`，预期输出包含完整敏感键值。

参考执行脚本（伪代码）：

```sh
chattool env cat
chattool env cat --no-mask
```

## 用例 2：列出可用 profile（list）

- 初始环境准备：
  - 在 `<tmp>/envs/` 下创建多个 `*.env` 文件。
- 相关文件：
  - `<tmp>/envs/profile1.env`
  - `<tmp>/envs/profile2.env`

预期过程和结果：
  1. 执行 `chattool env list`，预期输出包含 `profile1` 与 `profile2`。

参考执行脚本（伪代码）：

```sh
chattool env list
```

## 用例 3：保存 / 切换 / 删除 profile

- 初始环境准备：
  - 准备当前 `.env` 文件，包含已知内容。
- 相关文件：
  - `<tmp>/.env`
  - `<tmp>/envs/test_profile.env`

预期过程和结果：
  1. 执行 `chattool env save test_profile`，预期生成 `test_profile.env`，内容与当前 `.env` 一致。
  2. 修改当前 `.env` 内容后，执行 `chattool env use test_profile`，预期提示已激活，并恢复为保存内容。
  3. 执行 `chattool env delete test_profile`，预期 `test_profile.env` 被删除。

参考执行脚本（伪代码）：

```sh
chattool env save test_profile
chattool env use test_profile
chattool env delete test_profile
```

## 用例 4：初始化指定配置类型（init -t）

- 初始环境准备：
  - 注册一个测试用配置类型，包含普通键与敏感键。
- 相关文件：
  - `<tmp>/.env`

预期过程和结果：
  1. 执行 `chattool env init -i -t MockConfig` 并输入新值，预期 `.env` 被更新。
  2. 执行 `chattool env init -t NonExistent`，预期输出提示未匹配配置类型。

参考执行脚本（伪代码）：

```sh
chattool env init -i -t MockConfig
chattool env init -t NonExistent
```

## 用例 5：set/get/unset 基础链路

- 初始环境准备：
  - 准备当前 `.env` 文件。
- 相关文件：
  - `<tmp>/.env`

预期过程和结果：
  1. 执行 `chattool env set KEY=VALUE`，预期写入 `.env`。
  2. 执行 `chattool env get KEY`，预期输出对应值。
  3. 执行 `chattool env unset KEY`，预期清空该键。

参考执行脚本（伪代码）：

```sh
chattool env set KEY=VALUE
chattool env get KEY
chattool env unset KEY
```

## 清理 / 回滚

- 由临时目录自动回收，无需额外操作。
