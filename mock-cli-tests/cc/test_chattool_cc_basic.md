# chattool cc mock 基础用例

> 该组用例验证 `chattool cc` 的 CLI 编排与交互默认值处理，不触达真实飞书或 Agent 后端。

## Case 1: 帮助信息

### 初始环境准备

- 无

### 预期过程和结果

- 执行 `chattool cc --help` 返回 0
- 输出包含 `setup` / `init` / `start` 等子命令提示

### 参考执行脚本（伪代码）

```sh
chattool cc --help
```

## Case 2: 非交互生成配置

### 初始环境准备

- 创建临时目录作为 `work_dir`
- 选择临时路径作为 `config.toml`

### 预期过程和结果

- 执行 `chattool cc init -I --agent claudecode --platform feishu --quiet ...` 返回 0
- `config.toml` 被创建
- 配置文件包含 `[[projects]]` 与项目名称
- 配置文件写入项目级 `quiet = true`

### 参考执行脚本（伪代码）

```sh
chattool cc init -I \
  --agent claudecode \
  --platform feishu \
  --quiet \
  --project demo \
  --work-dir /tmp/work \
  --config /tmp/config.toml
```

## Case 3: 读取已有配置作为默认值

### 初始环境准备

- 准备已有 `config.toml`，包含项目/agent/platform/work_dir/quiet

### 预期过程和结果

- 执行 `chattool cc init -i --config <path>` 时先提示是否覆盖已有配置文件
- 覆盖确认选择否，立即退出成功，不再继续询问其它字段
- 覆盖确认选择是后，后续字段提示默认值来自已有配置
- 若已有 `quiet = true`，交互阶段会把 quiet 提示的默认值展示为开启
- 若已有平台凭证且选择不重新填写，生成的新配置会保留原有平台凭证
- 若沿用默认 quiet，生成的新配置会继续写入 `quiet = true`
- 该用例通过 monkeypatch 固定交互能力探测结果，不依赖真实 TTY。

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
- `app_secret` 直接以默认值形式提供，回车即可复用
- 生成的配置文件写入对应飞书凭证
- 该用例通过 monkeypatch 固定 `chatenv` 候选值来源，不要求本机提前写入真实飞书配置。

### 参考执行脚本（伪代码）

```sh
chatenv cat -t feishu
chattool cc init -i --agent claudecode --platform feishu --config /tmp/config.toml
```
