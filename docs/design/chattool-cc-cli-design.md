# ChatTool CC-Connect CLI 设计

> 目标：通过 `chattool cc` 统一完成 cc-connect 的安装、配置、运行与排障，让用户无需手写 TOML 即可快速用手机/IM 使用本地 Agent。

## 设计目标

- 一键可用：新手只需 1~3 个命令即可跑通最小可用链路
- 极简接口：一阶段只保留高频必需命令
- 与 `chattool setup` 协同：复用已有环境变量/安装逻辑
- 明确可见：配置、运行状态、日志可查询

## 非目标

- 不替代 cc-connect 的全部功能，仅提供高频能力的 CLI 抽象
- 不修改 cc-connect 核心行为，保持兼容官方配置

## 约定与路径

- cc-connect 配置文件默认：`~/.cc-connect/config.toml`
- 可通过 `--config` 指定配置路径（项目级配置）
- 所有写入涉及敏感信息时必须脱敏提示

## 命令总览（阶段一：最小可用）

```
chattool cc setup
chattool cc init
chattool cc start
chattool cc status
chattool cc logs
chattool cc doctor
```

## 命令设计

### 1) 安装与诊断

#### `chattool cc setup`
- 作用：安装/检查 cc-connect 运行依赖（Node.js/npm、cc-connect 包、平台 SDK）
- 选项：
  - `-i/--interactive`：强制交互
  - `-I/--no-interactive`：禁止交互，缺参时报错
  - 一阶段：自动处理依赖安装，不暴露额外开关（对齐 `chattool setup codex`）


#### `chattool cc doctor`
- 作用：快速自检（cc-connect 二进制、配置文件、平台 token、端口占用）
- 输出：列表式检查结果 + 失败原因 + 下一步建议

### 2) 初始化与配置

#### `chattool cc init`
- 作用：生成最小可用配置（Agent + Platform + Project）
- 选项：
  - `--project NAME`
  - `--agent TYPE`（claudecode/codex/cursor/gemini/opencode/iflow/qoder）
  - `--platform TYPE`（feishu/telegram/discord/slack/dingtalk/wecom/qq/line）
  - `--work-dir PATH`
  - `--config PATH`
  - `-i/--interactive`、`-I/--no-interactive`
- 行为：
  - 缺参时进入交互式问答
  - 自动合并已有 `config.toml`，避免覆盖
### 3) 运行与日志（最小可用）

#### `chattool cc start`
- 作用：调用 `cc-connect` 启动（默认读取 `~/.cc-connect/config.toml`）

#### `chattool cc status`
- 作用：展示运行概况（是否运行、项目数量、最近错误）

#### `chattool cc logs`
- 作用：显示/跟随日志
- 选项：
  - `--follow`
  - `--project NAME`

## 交互式流程（草案）

```
chattool cc init -i
1) 选择平台: feishu / telegram / discord / slack / ...
2) 选择 agent: claudecode / codex / cursor / ...
3) 输入项目名称与工作目录
4) 填写平台鉴权信息（敏感信息脱敏回显）
5) 生成配置并提示 "chattool cc start"
```

## 兼容性

- 生成的 `config.toml` 必须与 cc-connect 原生配置完全兼容
- 不额外引入 ChatTool 私有字段

## 后续实现建议

- `chattool cc setup` 复用 `src/chattool/setup/*` 逻辑
- TOML 读写复用 `chattool.config` 或引入专用 cc-connect config 模块
- 日志：默认输出 cc-connect stdout/stderr，同时可持久化到 `~/.cc-connect/cc-connect.log`
