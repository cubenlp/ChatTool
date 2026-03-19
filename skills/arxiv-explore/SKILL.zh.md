---
name: arxiv-explore
description: "通过 ChatTool CLI 搜索和探索 arXiv 论文。当用户询问搜索论文、获取每日最新提交、按 ID 获取论文，或使用 ai4math 等领域预设时使用。"
---

# arXiv 论文探索

## 快速开始

```bash
# 使用预设（推荐）
chattool explore arxiv daily -p ai4math
chattool explore arxiv daily -p math-formalization --days 3 -v

# 手动搜索
chattool explore arxiv search "cat:cs.AI AND all:transformer" -n 10

# 查看所有预设
chattool explore arxiv presets

# 按 ID 获取论文
chattool explore arxiv get 1706.03762
```

## 核心命令

### 预设列表

```bash
chattool explore arxiv presets
```

内置预设：

| 预设名 | 说明 |
|--------|------|
| `ai4math` | 定理证明、自动形式化、神经符号数学 |
| `math-formalization` | Lean/Coq/Isabelle + LLM 自动形式化 |
| `math-programming` | 符号计算、神经符号、代码化数学求解 |
| `math-reasoning` | LLM 数学推理基准、思维链、竞赛数学 |

### 每日论文

```bash
chattool explore arxiv daily [OPTIONS]
  -p, --preset NAME         使用命名预设（推荐）
  -c, --category CAT        分类过滤，可重复
  -k, --keyword KW          关键词过滤，可重复
  --days N                  获取最近 N 天（默认 1）
  -n, --max-results N       最大结果数（默认 200）
  -v, --verbose             显示摘要片段
```

示例：
```bash
chattool explore arxiv daily -p ai4math
chattool explore arxiv daily -p math-formalization --days 3
chattool explore arxiv daily -c cs.AI -c cs.LG --days 7 -v
```

### 搜索

```bash
chattool explore arxiv search [QUERY] [OPTIONS]
  -p, --preset NAME         使用命名预设
  -n, --max-results N       最大结果数（默认 10）
  -c, --category CAT        分类过滤，可重复
  -k, --keyword KW          关键词过滤，可重复
  --sort CRITERION          submittedDate|lastUpdatedDate|relevance
  -v, --verbose             显示摘要片段
```

查询语法：`cat:` `ti:` `abs:` `au:` `all:`，支持 `AND`/`OR`/`ANDNOT`

示例：
```bash
chattool explore arxiv search -p ai4math -n 30
chattool explore arxiv search "au:Avigad" --sort submittedDate -n 20
chattool explore arxiv search "ti:lean AND abs:formalization" -n 15 -v
```

### 按 ID 获取

```bash
chattool explore arxiv get ARXIV_ID [-v]
# -v 显示完整摘要
```

## Python API

```python
from chattool.explore.arxiv import ArxivClient, DailyFetcher, PRESETS, build_query, ArxivQuery

# --- 使用预设 ---
preset = PRESETS["ai4math"]
fetcher = DailyFetcher()

# 获取 + 精确过滤
raw = fetcher.since(days=1, categories=preset.categories, keywords=preset.query_keywords)
papers = preset.filter(raw)

# --- 手动搜索 ---
client = ArxivClient()
papers = client.search("cat:cs.LO AND all:lean4", max_results=20)

# 客户端过滤
filtered = client.filter_papers(papers, keywords=["theorem proving", "lean 4"])

# --- 查询构建器 ---
q = ArxivQuery().category("cs.AI").keyword("autoformalization").title("lean")
papers = client.search(q.build(), max_results=50)
```

## ai4math 领域覆盖

`ai4math` 预设覆盖：

**形式化验证 & 证明助手**
- autoformalization（自动形式化）、theorem proving（定理证明）
- interactive theorem proving（交互式定理证明）、formal proof
- Lean 4 / mathlib、Coq、Isabelle/HOL、Agda

**基准数据集**
- miniF2F、SorryDB、ProofNet、FIMO

**数学推理（精确）**
- math olympiad（数学竞赛）、tactic prediction（策略预测）
- premise selection（前提选择）、proof search（证明搜索）

**神经符号**
- neurosymbolic、neuro-symbolic、AlphaProof

**监控分类：** cs.AI, cs.LO, cs.CL, cs.PL, math.LO

## 注意事项

- arXiv API 限速：请求间隔 3 秒（自动执行）
- 每日论文在工作日 14:00 ET / 18:00 UTC 后更新；周末提交在周一批量出现
- 预设采用两阶段过滤：宽泛 API 查询 → 严格客户端过滤
- 使用 `-v` 查看摘要片段
