---
name: arxiv-explore
description: "Search and explore arXiv papers via ChatTool CLI. Use when user asks to search papers, get daily submissions, fetch specific arXiv papers by ID, or use domain presets like ai4math and math-formalization-weekly."
version: 0.1.0
---

# arXiv Explore

## Quick Start

```bash
# Use a preset (recommended)
chattool explore arxiv daily -p ai4math
chattool explore arxiv daily -p math-formalization --days 3 -v
chattool explore arxiv daily -p math-formalization-weekly --days 7 -v

# Manual search
chattool explore arxiv search "cat:cs.AI AND all:transformer" -n 10

# List available presets
chattool explore arxiv presets

# Fetch a specific paper
chattool explore arxiv get 1706.03762
```

## Domain Guides

- Weekly mathematical formalization tracking:
  see [references/math-formalization-weekly.md](references/math-formalization-weekly.md)
- Chinese version:
  see [references/math-formalization-weekly.zh.md](references/math-formalization-weekly.zh.md)
- Multi-query collector:
  `python skills/arxiv-explore/scripts/collect_math_formalization_weekly.py --days 7 --per-query 20`

## Core CLI

### Presets

```bash
chattool explore arxiv presets
```

Built-in presets:

| Preset | Description |
|--------|-------------|
| `ai4math` | Theorem proving, autoformalization, neurosymbolic math |
| `math-formalization` | Lean/Coq/Isabelle + LLM autoformalization |
| `math-formalization-weekly` | Weekly mathematical formalization tracking with broader recall |
| `math-programming` | Symbolic computation, neurosymbolic, code-based math |
| `math-reasoning` | LLM benchmarks, chain-of-thought, olympiad math |

### Daily Submissions

```bash
chattool explore arxiv daily [OPTIONS]
  -p, --preset NAME         Use a named preset (recommended)
  -c, --category CAT        Category to fetch (repeatable)
  -k, --keyword KW          Filter by keyword (repeatable)
  --days N                  Fetch from last N days (default: 1)
  -n, --max-results N       Max results (default: 200)
  -v, --verbose             Show abstract excerpt
```

Examples:
```bash
chattool explore arxiv daily -p ai4math
chattool explore arxiv daily -p math-formalization --days 3
chattool explore arxiv daily -p math-formalization-weekly --days 7 -v
chattool explore arxiv daily -c cs.AI -c cs.LG --days 7 -v
```

### Search

```bash
chattool explore arxiv search [QUERY] [OPTIONS]
  -p, --preset NAME         Use a named preset
  -n, --max-results N       Max number of results (default: 10)
  -c, --category CAT        Filter by category (repeatable)
  -k, --keyword KW          Filter by keyword (repeatable)
  --sort CRITERION          submittedDate|lastUpdatedDate|relevance
  -v, --verbose             Show abstract excerpt
```

Query syntax: `cat:`, `ti:`, `abs:`, `au:`, `all:`, combined with `AND`/`OR`/`ANDNOT`

Examples:
```bash
chattool explore arxiv search -p ai4math -n 30
chattool explore arxiv search -p math-formalization-weekly --sort submittedDate -n 50
chattool explore arxiv search "au:Avigad" --sort submittedDate -n 20
chattool explore arxiv search "ti:lean AND abs:formalization" -n 15 -v
```

## Math Formalization Weekly Workflow

Start with the weekly preset:

```bash
chattool explore arxiv daily -p math-formalization-weekly --days 7 -v
```

If results are too sparse, broaden recall:

```bash
chattool explore arxiv search -p math-formalization-weekly --sort submittedDate -n 80
chattool explore arxiv search "cat:cs.LO AND (all:lean4 OR all:mathlib OR all:coq OR all:isabelle)" --sort submittedDate -n 50
chattool explore arxiv search "cat:math.LO AND (all:formal mathematics OR all:theorem proving)" --sort submittedDate -n 50
```

If results are too noisy, narrow with title or abstract fields:

```bash
chattool explore arxiv search "ti:lean AND abs:autoformalization" --sort submittedDate -n 30 -v
chattool explore arxiv search "abs:\"interactive theorem proving\" AND (all:mathlib OR all:coq)" --sort submittedDate -n 30 -v
```

Recommended adjustment strategy:

1. Start from `daily -p math-formalization-weekly --days 7`.
2. If recall is low, broaden categories first (`cs.LO`, `cs.PL`, `math.LO`) before adding more short keywords.
3. If noise is high, switch from broad preset search to `ti:` / `abs:` queries.
4. When a subtopic emerges, search by system names (`lean4`, `mathlib`, `coq`, `isabelle`, `metamath`) and inspect abstracts with `-v`.
5. Use `get <ARXIV_ID>` for papers that look relevant enough to read in full.

For a recall-first weekly index with query families, real March 2026 examples, and a helper script, load [references/math-formalization-weekly.md](references/math-formalization-weekly.md).

### Get by ID

```bash
chattool explore arxiv get ARXIV_ID [-v]
# -v shows full abstract
```

## Python API

```python
from chattool.explore.arxiv import ArxivClient, DailyFetcher, PRESETS, build_query, ArxivQuery

# --- Presets ---
preset = PRESETS["ai4math"]
fetcher = DailyFetcher()

# Fetch + strict filter in one go
raw = fetcher.since(days=1, categories=preset.categories, keywords=preset.query_keywords)
papers = preset.filter(raw)

# --- Manual search ---
client = ArxivClient()
papers = client.search("cat:cs.LO AND all:lean4", max_results=20)

# Client-side filter
filtered = client.filter_papers(papers, keywords=["theorem proving", "lean 4"])

# --- Query builder ---
q = ArxivQuery().category("cs.AI").keyword("autoformalization").title("lean")
papers = client.search(q.build(), max_results=50)

# --- build_query convenience ---
q = build_query(
    categories=["cs.AI", "cs.LO"],
    keywords=["theorem proving", "lean4"],
)
papers = client.search(q, max_results=30)
```

## ai4math Domain Coverage

The `ai4math` preset covers:

**Formal verification & proof assistants**
- autoformalization, theorem proving, proof assistant
- interactive theorem proving, formal proof
- Lean 4 / mathlib, Coq, Isabelle/HOL, Agda

**Benchmarks & datasets**
- miniF2F, SorryDB, ProofNet, FIMO

**Math reasoning (specific)**
- math olympiad, tactic prediction, premise selection
- proof search, proof generation

**Neurosymbolic**
- neurosymbolic, neuro-symbolic, AlphaProof

**Categories monitored:** cs.AI, cs.LO, cs.CL, cs.PL, math.LO

## Notes

- arXiv API: 3s between requests (enforced automatically)
- Daily submissions appear after 14:00 ET / 18:00 UTC on weekdays; weekends batch on Monday
- Presets use two-stage filtering: broad API query → strict client-side filter
- Use `-v` to see abstract excerpts
