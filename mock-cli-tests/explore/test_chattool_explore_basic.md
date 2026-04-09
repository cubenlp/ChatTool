# test_chattool_explore_basic

测试 `chattool explore arxiv` 的 mock 基础链路，覆盖帮助信息、preset 搜索、daily 聚合、单篇获取与 preset 列表。

## 元信息

- 命令：`chattool explore arxiv <command> [args]`
- 目的：验证 `explore` 命令已接入主 CLI，且 `arxiv` 子命令的编排与输出链路可用。
- 标签：`cli`、`mock`
- 前置条件：无真实 arXiv 网络依赖；通过 mock `ArxivClient` / `DailyFetcher` 隔离外部请求。
- 环境准备：使用 `CliRunner` 调用统一入口 `chattool`。
- 回滚：无持久化文件写入，无需额外回滚。

## 用例 1：帮助信息可达

- 初始环境准备：
  - 无。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool explore --help`，预期输出包含 `arxiv` 子命令。
  2. 执行 `chattool explore arxiv --help`，预期输出包含 `search`、`daily`、`get`、`presets`。
  3. 执行 `chattool explore arxiv search --help`，预期输出包含 `--preset`、`--category`、`--keyword`。

参考执行脚本（伪代码）：

```sh
chattool explore --help
chattool explore arxiv --help
chattool explore arxiv search --help
```

## 用例 2：使用 preset 搜索论文

- 初始环境准备：
  - mock `build_query` 返回固定查询串。
  - mock `ArxivClient.search` 返回一篇示例论文。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool explore arxiv search -p ai4math -n 2`，预期 CLI 自动根据 preset 生成查询串。
  2. 预期输出包含论文数量与示例论文标题。

参考执行脚本（伪代码）：

```sh
chattool explore arxiv search -p ai4math -n 2
```

## 用例 3：daily 使用 preset 做严格过滤

- 初始环境准备：
  - mock `DailyFetcher.since` 返回多篇论文，其中仅一篇满足 preset 关键词过滤。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool explore arxiv daily -p math-formalization --days 3`。
  2. 预期输出仅保留符合 preset 的论文，并显示 `last 3 days` 标签。

参考执行脚本（伪代码）：

```sh
chattool explore arxiv daily -p math-formalization --days 3
```

## 用例 4：获取单篇论文并显示摘要

- 初始环境准备：
  - mock `ArxivClient.get_by_id` 返回指定论文对象。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool explore arxiv get 1706.03762 -v`。
  2. 预期输出包含论文标题与 `Abstract:` 段落。

参考执行脚本（伪代码）：

```sh
chattool explore arxiv get 1706.03762 -v
```

## 用例 4b：`get` 缺少 arXiv ID 时自动补问

- 初始环境准备：
  - mock `ArxivClient.get_by_id` 返回指定论文对象。
  - mock 交互输入 `1706.03762`。
- 相关文件：
  - 无

预期过程和结果：
  1. 在交互可用环境下执行 `chattool explore arxiv get`。
  2. CLI 应补问 arXiv ID，然后继续获取并输出论文信息。

## 用例 5：列出 preset 清单

- 初始环境准备：
  - 无。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool explore arxiv presets`，预期输出包含 `ai4math`、`math-formalization`、`math-formalization-weekly` 等 preset 名称与描述摘要。

参考执行脚本（伪代码）：

```sh
chattool explore arxiv presets
```

## 清理 / 回滚

- 无需额外操作。
