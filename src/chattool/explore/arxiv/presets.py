"""
arXiv search presets for common research domains.

Each preset defines:
  - categories:      arXiv category filters (server-side)
  - query_keywords:  keywords sent to arXiv API (broad, OR-combined)
  - filter_keywords: client-side strict filter applied after fetching
                     (paper must match at least one; uses exact phrase matching)

Usage::

    from chattool.explore.arxiv.presets import PRESETS
    cfg = PRESETS["ai4math"]

    # API search
    papers = client.search(cfg.query(), max_results=100)

    # Daily fetch + strict filter
    raw = fetcher.since(days=1, categories=cfg.categories, keywords=cfg.query_keywords)
    papers = cfg.filter(raw)
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SearchPreset:
    name: str
    description: str
    categories: List[str] = field(default_factory=list)
    # Sent to arXiv API — can be broad (short phrases ok at API level)
    query_keywords: List[str] = field(default_factory=list)
    # Applied client-side after fetch — must be precise multi-word phrases
    filter_keywords: List[str] = field(default_factory=list)

    # backward compat: treat .keywords as query_keywords
    @property
    def keywords(self) -> List[str]:
        return self.query_keywords

    def query(self) -> str:
        """Build arXiv query string (categories + query_keywords)."""
        from .query import build_query
        return build_query(categories=self.categories, keywords=self.query_keywords)

    def filter(self, papers: list) -> list:
        """Client-side strict filter: paper must be in a preset category
        AND match at least one filter_keyword in title or abstract."""
        if not self.filter_keywords and not self.categories:
            return papers
        result = []
        for p in papers:
            if self.categories and not any(p.in_category(c) for c in self.categories):
                continue
            if self.filter_keywords and not any(p.has_keyword(k) for k in self.filter_keywords):
                continue
            result.append(p)
        return result


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

PRESETS: dict = {}


def _register(preset: SearchPreset) -> SearchPreset:
    PRESETS[preset.name] = preset
    return preset


# ---------------------------------------------------------------------------
# ai4math — broad umbrella
# ---------------------------------------------------------------------------

_register(SearchPreset(
    name="ai4math",
    description="AI for Mathematics: formal verification, theorem proving, autoformalization, math reasoning",
    categories=["cs.AI", "cs.LO", "cs.CL", "cs.PL", "math.LO"],
    query_keywords=[
        "autoformalization", "theorem proving", "proof assistant",
        "lean4", "mathlib", "miniF2F", "SorryDB",
        "math olympiad", "neurosymbolic", "AlphaProof",
    ],
    filter_keywords=[
        # Formalization & ITP/ATP
        "autoformalization", "theorem proving", "proof assistant",
        "interactive theorem proving", "formal proof",
        "lean 4", "lean4", "mathlib", "coq proof", "isabelle/hol",
        "miniF2F", "SorryDB", "ProofNet", "FIMO",
        # Math reasoning (specific)
        "math olympiad", "olympiad math",
        "tactic prediction", "premise selection", "proof search",
        "tactic proof", "proof generation",
        # Neurosymbolic math
        "neurosymbolic", "neuro-symbolic",
        # Notable systems
        "AlphaProof", "DeepMind math",
    ],
))

# ---------------------------------------------------------------------------
# math-formalization — strict focus on ITP/ATP + LLM
# ---------------------------------------------------------------------------

_register(SearchPreset(
    name="math-formalization",
    description="Mathematical formalization: Lean/Coq/Isabelle + LLM autoformalization",
    categories=["cs.AI", "cs.LO", "cs.CL", "math.LO"],
    query_keywords=[
        "autoformalization", "theorem proving", "proof assistant",
        "lean4", "mathlib", "miniF2F", "SorryDB", "ProofNet",
        "interactive theorem proving",
    ],
    filter_keywords=[
        "autoformalization",
        "theorem proving",
        "proof assistant",
        "interactive theorem proving",
        "formal proof",
        "lean 4", "lean4", "mathlib",
        "coq proof", "isabelle",
        "miniF2F", "SorryDB", "ProofNet", "FIMO",
        "tactic prediction", "premise selection",
    ],
))

# ---------------------------------------------------------------------------
# math-formalization-weekly — broader weekly tracking for recent papers
# ---------------------------------------------------------------------------

_register(SearchPreset(
    name="math-formalization-weekly",
    description="Weekly tracking for mathematical formalization papers with broader recall and strict post-filtering",
    categories=["cs.AI", "cs.LO", "cs.CL", "cs.PL", "math.LO"],
    query_keywords=[
        "autoformalization",
        "formal mathematics",
        "formalized mathematics",
        "theorem proving",
        "proof assistant",
        "interactive theorem proving",
        "formal proof",
        "lean4",
        "mathlib",
        "coq",
        "isabelle",
        "hol light",
        "metamath",
        "premise selection",
        "proof search",
        "informal-to-formal",
    ],
    filter_keywords=[
        "autoformalization",
        "formal mathematics",
        "formalized mathematics",
        "mathematical formalization",
        "interactive theorem proving",
        "theorem proving",
        "formal proof",
        "proof assistant",
        "informal-to-formal",
        "lean 4",
        "lean4",
        "mathlib",
        "coq",
        "isabelle",
        "hol light",
        "metamath",
        "premise selection",
        "proof search",
        "tactic prediction",
        "proof generation",
        "miniF2F",
        "ProofNet",
        "FIMO",
        "formal theorem proving",
    ],
))

# ---------------------------------------------------------------------------
# math-programming — symbolic / neurosymbolic / code-based math
# ---------------------------------------------------------------------------

_register(SearchPreset(
    name="math-programming",
    description="Mathematical programming: symbolic computation, neurosymbolic, code-based math solving",
    categories=["cs.AI", "cs.CL", "cs.PL", "cs.SC"],
    query_keywords=[
        "symbolic computation", "computer algebra", "program synthesis",
        "neurosymbolic", "AlphaProof", "tactic",
    ],
    filter_keywords=[
        "symbolic computation", "computer algebra system",
        "program synthesis", "neurosymbolic", "neuro-symbolic",
        "mathematical programming", "symbolic math",
        "tactic proof", "proof search",
        "AlphaProof", "NeuroProlog",
    ],
))

# ---------------------------------------------------------------------------
# math-reasoning — LLM benchmark / chain-of-thought
# ---------------------------------------------------------------------------

_register(SearchPreset(
    name="math-reasoning",
    description="LLM mathematical reasoning: benchmarks, chain-of-thought, problem solving",
    categories=["cs.AI", "cs.CL", "cs.LG"],
    query_keywords=[
        "mathematical reasoning", "math olympiad",
        "GSM8K", "AIME", "AMC", "MATH benchmark",
    ],
    filter_keywords=[
        "mathematical reasoning", "math reasoning",
        "math olympiad", "MATH benchmark", "GSM8K", "AIME", "AMC",
        "math problem solving", "chain-of-thought math",
    ],
))
