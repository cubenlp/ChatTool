# arXiv Explore 模块设计文档

## 目标

提供对 arXiv 公共 API 的封装，支持论文搜索、元数据获取、批量收割等场景，
供调研和数据探索使用。

---

## API 概览

arXiv 提供两个公共接口，均无需认证：

| 接口 | 端点 | 适用场景 |
|------|------|---------|
| Query API | `http://export.arxiv.org/api/query` | 搜索、按 ID 获取、小批量查询 |
| OAI-PMH | `https://export.arxiv.org/oai2` | 大批量元数据收割、增量同步 |

没有官方 JSON API，返回格式均为 XML（Atom 1.0 / OAI-DC）。

---

## Query API

### 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `search_query` | 搜索表达式 | — |
| `id_list` | 逗号分隔的 arXiv ID | — |
| `start` | 分页偏移 | 0 |
| `max_results` | 单次返回数量，上限 2000 | 10 |
| `sortBy` | `relevance` / `lastUpdatedDate` / `submittedDate` | `relevance` |
| `sortOrder` | `descending` / `ascending` | `descending` |

### 搜索字段前缀

```
ti:   标题        au:   作者        abs:  摘要
cat:  分类        jr:   期刊        id:   arXiv ID
all:  全字段
```

布尔运算符：`AND` `OR` `ANDNOT`，支持括号分组。

### 示例

```
# 搜索 cs.AI 下的 transformer 论文，按提交时间倒序
http://export.arxiv.org/api/query?search_query=cat:cs.AI+AND+ti:transformer&sortBy=submittedDate&sortOrder=descending&max_results=20

# 按 ID 获取
http://export.arxiv.org/api/query?id_list=1706.03762,2005.14165
```

### 返回字段（每条 entry）

```
entry_id      arXiv 链接（含版本号）
title         标题
summary       摘要
authors       作者列表
categories    分类列表（主分类 + 交叉分类）
published     首次提交时间
updated       最后更新时间
pdf_url       PDF 链接
doi           DOI
comment       作者备注
journal_ref   期刊引用
```

### 限制

- 单次 `max_results` 上限 **2000**
- 深度分页总结果上限约 **300,000**
- 请求间隔建议 **≥ 3 秒**（官方要求）

---

## OAI-PMH API

适合需要同步整个分类或按日期范围批量收割的场景。

```
# 按日期范围收割 cs 分类
https://export.arxiv.org/oai2?verb=ListRecords&metadataPrefix=arXiv&set=cs&from=2024-01-01&until=2024-01-31

# 获取单条记录
https://export.arxiv.org/oai2?verb=GetRecord&identifier=oai:arXiv.org:1706.03762&metadataPrefix=arXiv
```

支持 `resumptionToken` 分页，元数据格式：`oai_dc` / `arXiv` / `arXivRaw`。

---

## 依赖选型

使用官方推荐的 `arxiv` 库作为底层，不重复造轮子：

```
arxiv >= 2.0
```

理由：
- 维护活跃，自动处理分页和速率限制（默认 3s 间隔）
- `Result` 对象字段完整
- 支持懒加载迭代，内存友好

OAI-PMH 收割场景直接用 `requests` + `xml.etree` 处理，无需额外依赖。

---

## 模块设计

```
explore/arxiv/
├── __init__.py
├── DESIGN.md          # 本文档
├── client.py          # ArxivClient：搜索、按 ID 获取
├── harvest.py         # OAI-PMH 批量收割
└── models.py          # Paper dataclass（统一字段）
```

### `models.py` — 统一数据模型

```python
@dataclass
class Paper:
    arxiv_id: str        # 不含版本号，如 "1706.03762"
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    published: datetime
    updated: datetime
    pdf_url: str
    doi: str | None
    comment: str | None
    journal_ref: str | None
```

### `client.py` — ArxivClient

```python
class ArxivClient:
    def search(query, max_results, sort_by, sort_order) -> list[Paper]
    def get_by_id(arxiv_id) -> Paper
    def get_by_ids(arxiv_ids) -> list[Paper]
    def search_iter(query, ...) -> Iterator[Paper]   # 懒加载，适合大量结果
```

### `harvest.py` — OAI 收割

```python
class ArxivHarvester:
    def harvest(category, from_date, until_date) -> Iterator[Paper]
    def harvest_since(category, from_date) -> Iterator[Paper]
```

---

## 使用条款要点

- 免费，无需注册或 API key
- 请求间隔 ≥ 3 秒
- 大批量收割用 OAI-PMH，不用 Query API
- 元数据 CC0 协议，可自由重用
- 需注明"感谢 arXiv 提供开放获取互操作性"
