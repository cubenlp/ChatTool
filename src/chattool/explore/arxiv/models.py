"""arXiv paper data model."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


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

    def __repr__(self):
        return f"Paper({self.arxiv_id!r}, {self.title!r})"
