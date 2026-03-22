# chattool cc 基础用例

## Case 1: 帮助信息

### 初始环境准备

- 无

### 预期过程和结果

- 执行 `chattool cc --help` 返回 0
- 输出包含 `init` / `start` 等子命令提示

### 参考执行脚本（伪代码）

```sh
chattool cc --help
```

## Case 2: 非交互生成配置

### 初始环境准备

- 创建临时目录作为 `work_dir`
- 选择临时路径作为 `config.toml`

### 预期过程和结果

- 执行 `chattool cc init -I --agent claudecode --platform feishu ...` 返回 0
- `config.toml` 被创建
- 配置文件包含 `[[projects]]` 与项目名称

### 参考执行脚本（伪代码）

```sh
chattool cc init -I \
  --agent claudecode \
  --platform feishu \
  --project demo \
  --work-dir /tmp/work \
  --config /tmp/config.toml
```

## Case 3: 读取已有配置作为默认值

### 初始环境准备

- 准备已有 `config.toml`，包含项目/agent/platform/work_dir

### 预期过程和结果

- 执行 `chattool cc init -i --config <path>` 时提示默认值来自已有配置
- 覆盖确认选择否，退出成功

### 参考执行脚本（伪代码）

```sh
chattool cc init -i --config /tmp/config.toml
```

## Case 4: 飞书初始化复用 chatenv 候选值

### 初始环境准备

- 当前 `chatenv` 已配置 `FEISHU_APP_ID` 与 `FEISHU_APP_SECRET`
- 使用新的临时 `config.toml`，确保没有已有平台配置可复用

### 预期过程和结果

- 执行 `chattool cc init -i --agent claudecode --platform feishu --config <path>` 返回 0
- 交互阶段提示检测到 `chatenv` 的飞书配置候选
- `app_id` 提示默认值来自 `FEISHU_APP_ID`
- 选择沿用默认 `app_secret` 后，生成的配置文件写入对应飞书凭证

### 参考执行脚本（伪代码）

```sh
chatenv cat -t feishu
chattool cc init -i --agent claudecode --platform feishu --config /tmp/config.toml
```
