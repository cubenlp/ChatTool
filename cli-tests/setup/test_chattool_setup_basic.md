# test_chattool_setup_basic

测试 `chattool setup` 的基础链路，覆盖 alias/chrome/frp/nodejs/codex/claude/opencode 等子命令入口。

## 元信息

- 命令：`chattool setup <command> [args]`
- 目的：验证 setup 工具的基础命令可用。
- 标签：`cli`
- 前置条件：无
- 环境准备：按需准备交互参数或依赖。
- 回滚：删除生成的配置或临时文件。

## 用例 1：帮助信息

- 初始环境准备：
  - 无
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool setup --help`，预期输出子命令列表。

参考执行脚本（伪代码）：

```sh
chattool setup --help
```

## 用例 2：alias

- 初始环境准备：
  - 准备临时 rc 文件路径（如 `.zshrc`）。
- 相关文件：
  - `<tmp>/.zshrc`

预期过程和结果：
  1. 执行 `chattool setup alias --dry-run`，预期输出 alias 变更内容且不写入文件。

参考执行脚本（伪代码）：

```sh
chattool setup alias --dry-run
```

## 用例 3：chrome/frp/nodejs

- 初始环境准备：
  - 确保可安装依赖。
- 相关文件：
  - 可能生成的安装目录或配置文件。

预期过程和结果：
  1. 执行 `chattool setup chrome -i`，预期进入交互式安装流程。
  2. 执行 `chattool setup frp -i`，预期进入交互式安装流程。
  3. 执行 `chattool setup nodejs -i`，预期进入交互式安装流程，并在缺少 `~/.nvm/nvm.sh` 时直接写入内置的 `nvm.sh`。

参考执行脚本（伪代码）：

```sh
chattool setup chrome -i
chattool setup frp -i
chattool setup nodejs -i
```

## 用例 4：codex/claude/opencode

- 初始环境准备：
  - 准备 API key 与 base_url。
- 相关文件：
  - 可能生成的配置文件。

预期过程和结果：
  1. 执行 `chattool setup codex -i`，预期进入交互式配置流程。
  2. 执行 `chattool setup claude -i`，预期进入交互式配置流程。
  3. 执行 `chattool setup opencode -i`，预期进入交互式配置流程。

参考执行脚本（伪代码）：

```sh
chattool setup codex -i
chattool setup claude -i
chattool setup opencode -i
```

## 清理 / 回滚

- 删除生成的配置文件或安装目录。
