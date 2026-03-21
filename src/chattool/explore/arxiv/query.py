"""arXiv query builder — construct structured search queries."""
from dataclasses import dataclass, field
from typing import List, Optional
import re


def _quote_if_needed(text: str) -> str:
    """Quote phrases for arXiv field queries when they contain whitespace."""
    if not text:
        return text
    if text.startswith('"') and text.endswith('"'):
        return text
    if re.search(r"\s", text):
        return '"' + text.replace('"', '\\"') + '"'
    return text


def _field(field: str, value: str) -> str:
    return f"{field}:{_quote_if_needed(value)}"


@dataclass
class ArxivQuery:
    """
    Fluent builder for arXiv search queries.

    Usage::

        q = ArxivQuery().category("cs.AI").keyword("transformer").title("attention")
        print(q.build())
        # cat:cs.AI AND all:transformer AND ti:attention
    """
    _parts: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Field filters
    # ------------------------------------------------------------------

    def category(self, cat: str) -> "ArxivQuery":
        """Filter by arXiv category, e.g. 'cs.AI', 'math.CO'."""
        self._parts.append(_field("cat", cat))
        return self

    def keyword(self, kw: str) -> "ArxivQuery":
        """Search all fields (title + abstract + ...) for a keyword."""
        self._parts.append(_field("all", kw))
        return self

    def title(self, text: str) -> "ArxivQuery":
        """Match text in title."""
        self._parts.append(_field("ti", text))
        return self

    def abstract(self, text: str) -> "ArxivQuery":
        """Match text in abstract."""
        self._parts.append(_field("abs", text))
        return self

    def author(self, name: str) -> "ArxivQuery":
        """Match author name."""
        self._parts.append(_field("au", name))
        return self

    def journal(self, ref: str) -> "ArxivQuery":
        """Match journal reference."""
        self._parts.append(_field("jr", ref))
        return self

    # ------------------------------------------------------------------
    # Boolean combinators
    # ------------------------------------------------------------------

    def AND(self, other: "ArxivQuery") -> "ArxivQuery":
        q = ArxivQuery()
        q._parts = [f"({self.build()}) AND ({other.build()})"]
        return q

    def OR(self, other: "ArxivQuery") -> "ArxivQuery":
        q = ArxivQuery()
        q._parts = [f"({self.build()}) OR ({other.build()})"]
        return q

    def NOT(self, other: "ArxivQuery") -> "ArxivQuery":
        q = ArxivQuery()
        q._parts = [f"({self.build()}) ANDNOT ({other.build()})"]
        return q

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self) -> str:
        return " AND ".join(self._parts)

    def __str__(self) -> str:
        return self.build()


def build_query(
    categories: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    title: Optional[str] = None,
    abstract: Optional[str] = None,
    author: Optional[str] = None,
) -> str:
    """
    Convenience function to build a query string from common filters.

    All provided filters are combined with AND.
    Multiple categories or keywords are combined with OR internally.

    Example::

        build_query(categories=["cs.AI", "cs.LG"], keywords=["LLM", "transformer"])
        # (cat:cs.AI OR cat:cs.LG) AND (all:LLM OR all:transformer)
    """
    parts = []
    if categories:
        parts.append("(" + " OR ".join(_field("cat", c) for c in categories) + ")")
    if keywords:
        parts.append("(" + " OR ".join(_field("all", k) for k in keywords) + ")")
    if title:
        parts.append(_field("ti", title))
    if abstract:
        parts.append(_field("abs", abstract))
    if author:
        parts.append(_field("au", author))
    return " AND ".join(parts)
