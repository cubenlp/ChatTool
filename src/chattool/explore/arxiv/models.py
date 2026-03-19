"""arXiv paper data model."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Paper:
    arxiv_id: str
    title: str
    summary: str
    authors: list
    categories: list
    published: datetime
    updated: datetime
    pdf_url: str
    doi: Optional[str] = None
    comment: Optional[str] = None
    journal_ref: Optional[str] = None

    @property
    def url(self) -> str:
        return f"https://arxiv.org/abs/{self.arxiv_id}"

    @property
    def primary_category(self) -> str:
        return self.categories[0] if self.categories else ""

    def has_keyword(self, keyword: str) -> bool:
        """Case-insensitive match against title + summary."""
        kw = keyword.lower()
        return kw in self.title.lower() or kw in self.summary.lower()

    def in_category(self, category: str) -> bool:
        """Check if paper belongs to a category (prefix match, e.g. 'cs.AI' or 'cs')."""
        return any(c == category or c.startswith(category + ".") for c in self.categories)

    def by_author(self, name: str) -> bool:
        """Case-insensitive author name match."""
        name_lower = name.lower()
        return any(name_lower in a.lower() for a in self.authors)

    def __repr__(self):
        return f"Paper({self.arxiv_id!r}, {self.title!r})"
