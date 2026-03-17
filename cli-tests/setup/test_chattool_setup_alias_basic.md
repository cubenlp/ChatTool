# chattool setup alias 基础用例

## 元信息

- 命令：`chattool setup alias [options]`
- 目的：验证 alias 生成、写入与 dry-run 行为。
- 标签：`cli`
- 前置条件：无
- 环境准备：使用临时目录模拟 shell rc 文件。
- 回滚：测试结束后临时目录自动删除。
- 来源：`tests/test_setup_alias.py`

## 状态

- TODO：需要确认真实 CLI 链路对交互式选择与 shell rc 写入的约束。

## 用例 1：alias 块渲染与替换

### 初始环境准备

- 创建临时 `.zshrc` 文件。

### 相关文件

- `<tmp>/.zshrc`

### 预期过程和结果

1. 生成 alias 块，预期包含 begin/end 标记与别名内容。
2. 将 alias 块写入 rc 文件，预期文件包含别名。
3. 再次写入新的 alias 块，预期旧别名被替换，新别名生效。

### 参考执行脚本（伪代码）

```sh
chattool setup alias --dry-run
```

### 清理 / 回滚

- 由临时目录自动回收，无需额外操作。

## 用例 2：删除 alias 块

### 初始环境准备

- 创建临时 `.bashrc` 文件并写入 alias 块。

### 相关文件

- `<tmp>/.bashrc`

### 预期过程和结果

1. 清空 alias 块内容并写入，预期 rc 文件中不再包含 begin/end 标记。

### 参考执行脚本（伪代码）

```sh
chattool setup alias --dry-run
```

### 清理 / 回滚

- 由临时目录自动回收，无需额外操作。

## 用例 3：dry-run 不写入

### 初始环境准备

- 创建临时 `.zshrc` 文件。

### 相关文件

- `<tmp>/.zshrc`

### 预期过程和结果

1. 执行 `chattool setup alias --dry-run`，预期文件不变且输出包含别名内容。

### 参考执行脚本（伪代码）

```sh
chattool setup alias --dry-run
```

### 清理 / 回滚

- 由临时目录自动回收，无需额外操作。
