# Explore 数据探索

`chattool explore` 用于接入外部公开数据源，当前已提供 `arxiv` 子命令，用于论文搜索、按日抓取和 preset 检索。

## 快速开始

```bash
chattool explore arxiv search "cat:cs.AI AND ti:transformer" -n 5
chattool explore arxiv search -p ai4math -n 20
chattool explore arxiv daily -p math-formalization --days 3
chattool explore arxiv get 1706.03762 -v
chattool explore arxiv presets
```

## 命令

- `chattool explore arxiv search [QUERY]`：按 query 或 preset 搜索论文
- `chattool explore arxiv daily`：按最近 N 天抓取论文，并支持 preset 过滤
- `chattool explore arxiv get <ARXIV_ID>`：获取单篇论文详情
- `chattool explore arxiv presets`：列出内置研究主题 preset

## arXiv preset

内置 preset 面向固定研究方向，目前包括：

- `ai4math`
- `math-formalization`
- `math-programming`
- `math-reasoning`

当只提供 `--preset` 时，CLI 会自动构造 arXiv 查询；`daily` 还会在抓取后执行更严格的本地关键词过滤，以减少噪声结果。

## 说明

- `search` 支持直接使用 arXiv 原生字段语法，如 `ti:`、`au:`、`abs:`、`cat:`、`all:`。
- `daily` 至少需要 `--preset` 或一个 `-c/--category`。
- 设计细节见 [`docs/design/explore-arxiv.md`](../../design/explore-arxiv.md)。
