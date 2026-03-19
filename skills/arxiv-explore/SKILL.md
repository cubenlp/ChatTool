---
name: arxiv-explore
description: "Search and explore arXiv papers via ChatTool CLI. Use when user asks to search papers, get daily submissions, or fetch specific arXiv papers by ID."
---

# arXiv Explore

## Quick Start

1. Search papers by query:
   `chattool explore arxiv search "cat:cs.AI AND all:transformer" -n 10`
2. Get daily submissions:
   `chattool explore arxiv daily -c cs.AI -c cs.LG`
3. Fetch a specific paper:
   `chattool explore arxiv get 1706.03762`

## Core CLI

### Search

```bash
chattool explore arxiv search QUERY [OPTIONS]
  -n, --max-results N       Max number of results (default: 10)
  -c, --category CAT        Filter by category (repeatable)
  -k, --keyword KW          Filter by keyword (repeatable)
  --sort CRITERION          Sort by: submittedDate|lastUpdatedDate|relevance
  -v, --verbose             Show abstract excerpt
```

**Query syntax:**
- `cat:cs.AI` — category filter
- `ti:transformer` — title match
- `abs:attention` — abstract match
- `au:Vaswani` — author name
- `all:LLM` — search all fields
- Combine with `AND`, `OR`, `ANDNOT`

**Examples:**
```bash
# Search by category and keyword
chattool explore arxiv search "cat:cs.AI AND ti:transformer" -n 20

# Search with post-filtering
chattool explore arxiv search "all:diffusion" -c cs.CV -k "image generation"

# Search by author
chattool explore arxiv search "au:Hinton" --sort submittedDate -n 50
```

### Daily Submissions

```bash
chattool explore arxiv daily [OPTIONS]
  -c, --category CAT        Category to fetch (required, repeatable)
  -k, --keyword KW          Filter by keyword (repeatable)
  --days N                  Fetch from last N days (default: 1)
  -n, --max-results N       Max results (default: 200)
  -v, --verbose             Show abstract excerpt
```

**Examples:**
```bash
# Today's cs.AI papers
chattool explore arxiv daily -c cs.AI

# Last 3 days, multiple categories
chattool explore arxiv daily -c cs.AI -c cs.LG -c cs.CL --days 3

# Filter by keyword
chattool explore arxiv daily -c cs.CV -k diffusion -k "text-to-image"
```

### Get by ID

```bash
chattool explore arxiv get ARXIV_ID [-v]
```

**Example:**
```bash
chattool explore arxiv get 1706.03762 -v
```

## Python API

```python
from chattool.explore.arxiv import ArxivClient, DailyFetcher, build_query

# Search
client = ArxivClient()
papers = client.search("cat:cs.AI AND all:LLM", max_results=10)

# Filter results
filtered = client.filter_papers(papers, keywords=["language model"])

# Daily submissions
fetcher = DailyFetcher()
today = fetcher.today(categories=["cs.AI", "cs.LG"])
last_week = fetcher.since(days=7, categories=["cs.CV"], keywords=["diffusion"])

# Query builder
from chattool.explore.arxiv import ArxivQuery
q = ArxivQuery().category("cs.AI").keyword("transformer").title("attention")
papers = client.search(q.build())
```

## Common Use Cases

### Daily Digest

Get today's papers in your research areas:
```bash
chattool explore arxiv daily -c cs.AI -c cs.LG -c cs.CL -v > daily-digest.txt
```

### Topic Monitoring

Track specific topics over time:
```bash
chattool explore arxiv daily -c cs.CV -k "diffusion model" --days 7
```

### Author Tracking

Find recent papers by specific authors:
```bash
chattool explore arxiv search "au:Bengio" --sort submittedDate -n 20
```

### Cross-Category Search

Find papers spanning multiple areas:
```bash
chattool explore arxiv search "(cat:cs.AI OR cat:cs.LG) AND all:reinforcement" -n 30
```

## Notes

- arXiv API has rate limits: 3 seconds between requests (enforced by default)
- Search results are capped at ~300,000 total (deep pagination limited)
- Daily submissions appear after 14:00 ET / 18:00 UTC on weekdays
- Weekend submissions appear on Monday
- Use `-v` flag to see abstract excerpts in output
