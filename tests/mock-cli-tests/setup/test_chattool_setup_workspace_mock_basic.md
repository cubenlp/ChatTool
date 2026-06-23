# test_chattool_setup_workspace_mock_basic

验证 `chattool setup workspace` 的 mock CLI 行为：workspace 模板以 `AGENTS.md`、`TODO.md`、`ARCHIVE.md` 为外层控制文件，并且额外 workspace 模块遵守当前 ChatArch 插件模型。

## Case: 交互式 extra modules 支持 ChatTool、ChatBlog、ChatMemory

### 初始环境准备

- 使用 `CliRunner` 调用 `chattool setup workspace`。
- mock 交互输入 workspace 路径。
- mock extra module 选择返回 `chattool`、`chatblog`、`memory`。
- mock 各 module apply 函数，避免真实 clone。

### 预期过程和结果

- 命令成功完成。
- 输出 `Enabled options: chattool, chatblog, memory`。
- `chatblog` 替代旧 `rexblog`；输出应包含 `ChatBlog repo:`，不应再包含 `RexBlog repo:`。
- `memory` 表示 `ChatMemory` workspace 附带插件；输出应包含 `ChatMemory repo:`。

```sh
run chattool setup workspace in interactive mode
select extra modules chattool, chatblog, memory
expect successful output and no rexblog wording
```

## Case: ChatMemory clone/update 无权限时跳过

### 初始环境准备

- mock extra module 只选择 `memory`。
- mock ChatMemory clone/update 抛出可恢复的 ClickException，例如无 clone 权限或仓库不可达。

### 预期过程和结果

- workspace 初始化仍成功完成。
- 输出 `Enabled options: memory`。
- 输出清楚说明 ChatMemory 被跳过，例如 `ChatMemory skipped:`。
- 不创建 `skills/chatarch` symlink。

```sh
run chattool setup workspace in interactive mode
select memory
simulate ChatMemory clone failure
expect command success and skipped message
```

## Case: ChatMemory 不覆盖已有真实 skills/chatarch 目录

### 初始环境准备

- 在 workspace 中预先创建真实目录 `skills/chatarch`。
- 构造 fake ChatMemory repo，包含 `Skills/chatarch`。
- 调用 `apply_memory_option()`。

### 预期过程和结果

- 操作失败并提示拒绝替换已有 non-symlink path。
- 原 `skills/chatarch` 目录和其中内容保留。

```sh
prepare workspace/skills/chatarch as a real directory
call apply_memory_option
expect ClickException and original files remain
```
