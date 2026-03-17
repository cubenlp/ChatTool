# chattool env 基础用例

## 元信息

- 命令：`chatenv <command>`
- 目的：验证环境配置文件的查看、列表、保存、切换与删除的 CLI 基本链路。
- 标签：`cli`
- 前置条件：无
- 环境准备：使用临时目录模拟环境配置目录与 `.env` 文件。
- 回滚：测试结束后临时目录自动删除。

## 用例 1：查看当前环境配置（cat）

### 初始环境准备

- 创建临时目录作为环境配置根目录。
- 创建 `.env` 文件，包含普通键与敏感键。

### 相关文件

- `<tmp>/.env`
- `<tmp>/envs/*.env`

### 预期过程和结果

1. 执行 `chatenv cat`，预期输出包含普通键，敏感键已按规则脱敏。
2. 执行 `chatenv cat --no-mask`，预期输出包含完整敏感键值。

### 参考执行脚本（伪代码）

```sh
chatenv cat
chatenv cat --no-mask
```

### 清理 / 回滚

- 由临时目录自动回收，无需额外操作。

## 用例 2：列出可用 profile（list）

### 初始环境准备

- 在 `<tmp>/envs/` 下创建多个 `*.env` 文件。

### 相关文件

- `<tmp>/envs/profile1.env`
- `<tmp>/envs/profile2.env`

### 预期过程和结果

1. 执行 `chatenv list`，预期输出包含 `profile1` 与 `profile2`。

### 参考执行脚本（伪代码）

```sh
chatenv list
```

### 清理 / 回滚

- 由临时目录自动回收，无需额外操作。

## 用例 3：保存 / 切换 / 删除 profile

### 初始环境准备

- 准备当前 `.env` 文件，包含已知内容。

### 相关文件

- `<tmp>/.env`
- `<tmp>/envs/test_profile.env`

### 预期过程和结果

1. 执行 `chatenv save test_profile`，预期生成 `test_profile.env`，内容与当前 `.env` 一致。
2. 修改当前 `.env` 内容后，执行 `chatenv use test_profile`，预期提示已激活，并恢复为保存内容。
3. 执行 `chatenv delete test_profile`，预期 `test_profile.env` 被删除。

### 参考执行脚本（伪代码）

```sh
chatenv save test_profile
chatenv use test_profile
chatenv delete test_profile
```

### 清理 / 回滚

- 由临时目录自动回收，无需额外操作。

## 用例 4：初始化指定配置类型（init -t）

### 初始环境准备

- 注册一个测试用配置类型，包含普通键与敏感键。

### 相关文件

- `<tmp>/.env`

### 预期过程和结果

1. 执行 `chatenv init -i -t MockConfig` 并输入新值，预期 `.env` 被更新。
2. 执行 `chatenv init -t NonExistent`，预期输出提示未匹配配置类型。

### 参考执行脚本（伪代码）

```sh
chatenv init -i -t MockConfig
chatenv init -t NonExistent
```

### 清理 / 回滚

- 由临时目录自动回收，无需额外操作。
